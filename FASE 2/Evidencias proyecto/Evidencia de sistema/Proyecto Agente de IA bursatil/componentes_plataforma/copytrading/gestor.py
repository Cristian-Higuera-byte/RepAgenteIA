# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara gestor .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Área de gestor del copy trading: requisitos para publicar, mis estrategias (crear, editar, publicar, pausar y cerrar) y mis seguidores.

La lógica y las reglas están en `herramientas/gestor_estrategias.py`; aquí solo se dibuja y se llama a esas funciones. Cada acción deja un aviso en
`st.session_state` que la vista muestra una vez (éxito o el motivo legible por el que no se pudo). Los estilos (ges-*) están en estilos.css.
El copy trading es por ahora solo demo y para publicar hay que aceptar compartir el historial de operaciones con el apodo como nombre público.
"""
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

import configuracion
from herramientas import gestor_estrategias as gestion

# Clave de session_state con el aviso de la última acción ((tipo, texto); se muestra una vez)
_CLAVE_AVISO = "gestor_aviso"
# Texto y estilo de cada estado de una estrategia
_ESTADOS = {"borrador": ("Borrador", "b"), "publicada": ("Publicada", "p"), "pausada": ("Pausada", "m"), "cerrada": ("Cerrada", "c")}
_TIPOS_TEXTO = {"manual": "Manual", "algoritmico": "Algorítmico"}


# TITULO AVISAR

def _avisar(tipo: str, texto: str) -> None:
    """Deja en session_state el aviso que se mostrará en la próxima pintada ("ok" o "error")."""
    st.session_state[_CLAVE_AVISO] = (tipo, texto)


# TITULO EJECUTAR ACCION

def _accion(funcion, *argumentos, exito: str) -> None:
    """Ejecuta una acción de `gestor_estrategias` y deja el aviso: `exito` si sale bien o el mensaje del error si lanza `ErrorGestor`. Sirve de `on_click`."""
    try:
        funcion(*argumentos)
        _avisar("ok", exito)
    except gestion.ErrorGestor as e:
        _avisar("error", str(e))
    except Exception:  # noqa: BLE001 - un fallo inesperado no debe romper la vista
        _avisar("error", "No se pudo completar la acción. Inténtalo de nuevo.")


# TITULO REQUISITOS

def _requisitos(req: dict) -> None:
    """Dibuja la lista de requisitos para publicar, cada uno con ✓ o ✗ y su detalle."""
    filas = "".join(f"<div class='ges-req'><span class='{'ok' if i['ok'] else 'no'}'>{'✓' if i['ok'] else '✗'}</span><span class='t'>{escape(i['texto'])}</span>"
                    f"<span class='d'>{escape(i['detalle'])}</span></div>" for i in req["items"])
    estado = ("<div class='ges-nota ok'>Cumples todos los requisitos: puedes publicar estrategias.</div>" if req["cumple"]
              else "<div class='ges-nota'>Puedes guardar borradores, pero para publicar tienes que cumplir todos los requisitos.</div>")
    st.html(f"<div class='ges-seccion'>Requisitos para publicar</div>{filas}{estado}")


# TITULO TARJETA DE ESTRATEGIA

def _cabecera(e: dict) -> str:
    """HTML de la cabecera de una estrategia propia: nombre, estado, tipo y sus cifras principales."""
    texto, cls = _ESTADOS.get(e["estado"], (e["estado"], "b"))
    m = e["metricas"] or {}
    rent = m.get("rent_1m")
    cifras = (f"Rentabilidad 1 mes: <b>{float(rent):.2f}%</b> · " if rent is not None else "") + \
             f"Inversores: <b>{e['copias']}</b> · Comisión: <b>{float(e['comision_pct']):g}%</b> · Inversión mínima: <b>${float(e['inversion_minima']):,.0f}</b> · " \
             f"Comisiones ganadas: <b>${e['ganado']:,.2f}</b>" + (f" · Por cobrar: <b>${e['por_cobrar']:,.2f}</b>" if e.get("por_cobrar") else "")
    return (f"<div class='ges-cab'><span class='ges-nombre'>{escape(e['nombre'])}</span><span class='ges-estado {cls}'>{texto}</span>"
            f"<span class='ges-tipo'>{_TIPOS_TEXTO.get(e['tipo'], '')}</span></div><div class='ges-cifras'>{cifras}</div>")


# TITULO ACCIONES DE UNA ESTRATEGIA

def _acciones(uid, e: dict) -> None:
    """Botones de una estrategia propia según su estado: publicar (con el consentimiento; si falta un requisito, el aviso dice cuál), pausar, reanudar y cerrar (con confirmación)."""
    eid, estado = e["id"], e["estado"]
    if estado == "cerrada":
        return
    columnas = st.columns([3, 1.3, 1.3, 2.4], vertical_alignment="bottom")
    if estado == "borrador":
        acepto = columnas[0].checkbox("Acepto compartir mi historial de operaciones (se mostrará con mi apodo)", key=f"ges_acepto_{eid}")
        columnas[1].button("Publicar", key=f"ges_publicar_{eid}", type="primary", width="stretch", disabled=not acepto,
                           on_click=_accion, args=(gestion.cambiar_estado, uid, eid, "publicada", True), kwargs={"exito": "Estrategia publicada. Ya aparece en el listado."})
    elif estado == "publicada":
        columnas[1].button("Pausar", key=f"ges_pausar_{eid}", width="stretch", on_click=_accion, args=(gestion.cambiar_estado, uid, eid, "pausada"),
                           kwargs={"exito": "Estrategia pausada: ya no admite copias nuevas."})
    elif estado == "pausada":
        columnas[1].button("Reanudar", key=f"ges_reanudar_{eid}", type="primary", width="stretch", on_click=_accion, args=(gestion.cambiar_estado, uid, eid, "publicada"),
                           kwargs={"exito": "Estrategia reanudada."})
    confirma = columnas[2].checkbox("Confirmo cerrar", key=f"ges_confirma_{eid}", help="Cerrar es definitivo: la estrategia no vuelve a abrirse.")
    columnas[3].button("Cerrar estrategia", key=f"ges_cerrar_{eid}", width="stretch", disabled=not confirma, on_click=_accion,
                       args=(gestion.cambiar_estado, uid, eid, "cerrada"), kwargs={"exito": "Estrategia cerrada."})


# TITULO FORMULARIO

def _campos(valores: dict, clave: str, bloquear_condiciones: bool = False) -> dict:
    """Dibuja los campos de una estrategia (nombre, tipo, categoría, biografía, descripción, comisión e inversión mínima) con los `valores` iniciales y devuelve lo ingresado.

    `clave` distingue los widgets de cada formulario; con `bloquear_condiciones` la comisión y la inversión mínima quedan deshabilitadas (hay inversores activos)."""
    cfg = configuracion.COPYTRADING
    c1, c2, c3 = st.columns(3)
    nombre = c1.text_input("Nombre de la estrategia", value=valores.get("nombre", ""), max_chars=40, key=f"{clave}_nombre")
    tipo = c2.selectbox("Tipo", list(_TIPOS_TEXTO), index=list(_TIPOS_TEXTO).index(valores.get("tipo") or "manual"), format_func=_TIPOS_TEXTO.get, key=f"{clave}_tipo")
    categorias = ["Sin categoría"] + cfg["categorias"]
    categoria = c3.selectbox("Categoría", categorias, index=categorias.index(valores["categoria"]) if valores.get("categoria") in categorias else 0, key=f"{clave}_categoria")
    biografia = st.text_area("Biografía del gestor (opcional)", value=valores.get("biografia", ""), max_chars=500, height=80, key=f"{clave}_bio")
    descripcion = st.text_area("Descripción de la estrategia", value=valores.get("descripcion", ""), max_chars=1000, height=110, key=f"{clave}_desc",
                               help="Cuenta qué operas, cómo y con qué gestión del riesgo.")
    c4, c5 = st.columns(2)
    comision = c4.number_input(f"Comisión de rendimiento (%, de 0 a {cfg['comision_max']:g})", min_value=0.0, max_value=float(cfg["comision_max"]), step=0.5,
                               value=float(valores.get("comision_pct", cfg["comision_defecto"])), disabled=bloquear_condiciones, key=f"{clave}_comision",
                               help="Porcentaje de la ganancia nueva de cada inversor que se te paga.")
    minimo = c5.number_input("Inversión mínima (USD)", min_value=float(cfg["inversion_minima"]), max_value=100000.0, step=10.0,
                             value=float(valores.get("inversion_minima", cfg["inversion_minima"])), disabled=bloquear_condiciones, key=f"{clave}_minimo")
    if bloquear_condiciones:
        st.caption("Con inversores activos no se puede cambiar la comisión ni la inversión mínima.")
    return {"nombre": nombre, "tipo": tipo, "categoria": None if categoria == "Sin categoría" else categoria, "biografia": biografia, "descripcion": descripcion,
            "comision_pct": comision, "inversion_minima": minimo}


# TITULO EDITAR

def _editar(uid, e: dict) -> None:
    """Formulario para editar una estrategia propia (no cerrada); guarda con `gestion.actualizar`."""
    with st.expander("Editar"), st.form(f"ges_editar_{e['id']}", border=False):
        datos = _campos(e, f"ges_ed_{e['id']}", bloquear_condiciones=e["copias"] > 0)
        if st.form_submit_button("Guardar cambios", icon=":material/save:"):
            _accion(gestion.actualizar, uid, e["id"], datos, exito="Cambios guardados.")
            st.rerun()


# TITULO SEGUIDORES

def _seguidores(uid, e: dict) -> None:
    """Muestra los inversores de una estrategia (solo apodo, monto, modo y estado) y lo ganado en comisiones."""
    with st.expander(f"Inversores y comisiones ({e['copias']} activos)"):
        try:
            filas = gestion.seguidores(uid, e["id"])
        except gestion.ErrorGestor as err:
            st.error(str(err))
            return
        except Exception:  # noqa: BLE001 - un fallo de lectura no debe romper el resto del área
            st.error("No se pudo consultar a los inversores. Inténtalo de nuevo en un momento.")
            return
        st.html(f"<div class='ges-cifras'>Comisiones cobradas en total: <b>${e['ganado']:,.2f}</b></div>")
        if not filas:
            st.info("Todavía nadie copia esta estrategia.")
            return
        tabla = []
        for f in filas:
            try:
                desde = datetime.fromisoformat(str(f["desde"]).replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y")
            except (KeyError, ValueError):
                desde = ""
            tabla.append({"Inversor": f["inversor"], "Asignación": f"${float(f['importe']):,.0f}" if f.get("importe") else f"x{float(f['multiplicador'] or 0):g}",
                          "Modo": "Importe" if f.get("modo") == "importe" else "Multiplicador", "Estado": str(f.get("estado", "")).capitalize(), "Desde": desde})
        st.dataframe(pd.DataFrame(tabla), hide_index=True, width="stretch")


# TITULO CREAR

def _crear(uid, req: dict, hay_estrategias: bool) -> None:
    """Formulario para crear una estrategia: se guarda como borrador o se publica directamente (si se cumplen los requisitos y se acepta compartir el historial)."""
    with st.expander("Crear una estrategia", expanded=not hay_estrategias), st.form("ges_crear", border=False):
        datos = _campos({}, "ges_nueva")
        acepto = st.checkbox("Acepto compartir mi historial de operaciones con otros usuarios (se mostrará con mi apodo, sin datos personales)", key="ges_nueva_acepto")
        b1, b2, _ = st.columns([1, 1, 2])
        borrador = b1.form_submit_button("Guardar borrador", icon=":material/draft:")
        publicar = b2.form_submit_button("Publicar", type="primary", icon=":material/publish:")
        if borrador or publicar:
            _accion(gestion.crear, uid, {**datos, "acepto_compartir": acepto}, publicar, exito="Estrategia publicada." if publicar else "Borrador guardado.")
            st.rerun()


# TITULO RENDERIZAR AREA GESTOR

def renderizar_area_gestor() -> None:
    """Dibuja el área de gestor: requisitos, mis estrategias con sus acciones y el formulario para crear una nueva. No devuelve nada."""
    if not gestion.disponible():
        st.info("El área de gestor necesita la base de datos (Supabase), que no está configurada en este equipo.")
        return
    usuario = st.session_state.get("usuario_informacion") or {}
    uid = usuario.get("id") if isinstance(usuario, dict) else None
    if uid is None:
        st.info("Inicia sesión para usar el área de gestor.")
        return
    aviso = st.session_state.pop(_CLAVE_AVISO, None)
    if aviso:
        (st.success if aviso[0] == "ok" else st.error)(aviso[1])
    try:
        req, mias = gestion.requisitos(uid), gestion.mis_estrategias(uid)
    except Exception:  # noqa: BLE001
        st.error("No se pudo consultar tu información. Inténtalo de nuevo en un momento.")
        return
    _requisitos(req)
    st.html("<div class='ges-seccion'>Mis estrategias</div>")
    if not mias:
        st.info("Todavía no tienes estrategias. Crea la primera más abajo.")
    for e in mias:
        with st.container(border=True):
            st.html(_cabecera(e))
            _acciones(uid, e)
            if e["estado"] != "cerrada":
                _editar(uid, e)
            _seguidores(uid, e)
    _crear(uid, req, bool(mias))



# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara gestor .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
