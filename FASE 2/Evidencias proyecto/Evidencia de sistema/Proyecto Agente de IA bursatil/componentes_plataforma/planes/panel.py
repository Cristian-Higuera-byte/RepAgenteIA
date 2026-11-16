# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara panel .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vista "Planes": muestra los planes (con el diseño de la vitrina) con su precio y preguntas por semana, y registra qué plan le interesa a cada usuario (prueba de demanda).

IMPORTANTE: todavía no hay pasarela de pago (Flow). Un plan de pago no se activa: «Contratar» solo deja registrado el interés. Con PLANES_LIBRES (desarrollo), al pulsar «Usar este plan» la cuenta pasa a ese
plan al instante (se guarda con `herramientas/cuota_ia.py`: en Supabase en multiusuario, en un archivo en modo local) y la plataforma cambia sus
límites y funciones según `herramientas/plan_funciones.json`. Además se registra el interés, se explica que es una medición y se ofrece avisar
cuando esté disponible y una encuesta corta de dos preguntas. Los eventos se guardan con `herramientas/demanda.py` y se ven resumidos en el
Laboratorio (pestaña Demanda). Cada tarjeta ofrece además «Comprar con billetera», que cobra el precio del saldo virtual de `herramientas/billetera.py` y activa el plan con
origen «pago». Debajo de las tarjetas hay un cuadro que compara todas las funciones de los cuatro planes.

Cada usuario ve siempre la misma variante de precio de cada plan (`configuracion.PLANES_IA[plan]["precios"]`), para comparar qué precio genera
más clics. A esta vista se llega desde el menú lateral o desde el botón «Ver planes» de la barra de uso del agente cuando la cuota está alta
o agotada; el origen se guarda con cada clic.
"""
import uuid
from html import escape
from pathlib import Path

import streamlit as st

import configuracion
from componentes_plataforma import _estaticos, vitrina_planes
from herramientas import billetera, cuota_ia, demanda, permisos_plan

# Hoja de estilos de la vista y textos de cada plan (planes.json), junto a este archivo
_CSS = Path(__file__).parent / "estilos.css"
_TEXTOS = _estaticos.datos_json(Path(__file__).parent / "planes.json")
# Clave de session_state con el origen de la visita actual: (origen, identificador de la visita)
_CLAVE_ORIGEN = "planes_origen"
# Clave de session_state con el plan por el que el usuario mostró interés en esta visita
_CLAVE_INTERES = "planes_interes"
# Claves de session_state con el aviso del último cambio de plan y el error de la última compra con la billetera (se muestran una vez)
_CLAVE_AVISO = "planes_aviso"
_CLAVE_ERROR = "planes_error"


# TITULO IR A PLANES

def ir_a_planes(origen: str) -> None:
    """Lleva al usuario a la vista de Planes y recuerda desde dónde llegó (`menu`, `barra_cuota` o `cuota_agotada`).

    Se usa como `on_click` de los botones: Streamlit lo ejecuta antes de volver a correr el script. Cada llamada abre una visita nueva."""
    st.session_state.navegacion_activo = "planes"
    st.session_state[_CLAVE_ORIGEN] = (origen, uuid.uuid4().hex[:8])
    st.session_state.pop(_CLAVE_INTERES, None)


# TITULO DIALOGO BLOQUEO

@st.dialog("Función con candado", width="small")
def dialogo_bloqueo(clave: str) -> None:
    """Ventana que avisa que una función solo está disponible desde cierto plan, con el botón «Ir al plan correspondiente».

    Recibe la clave de la función de `herramientas/plan_funciones.json` que el usuario intentó usar. Muestra el texto de
    `permisos_plan.mensaje_bloqueo` y, al pulsar el botón, lleva a la vista de Planes (el origen `bloqueo` queda en el registro de demanda)."""
    st.markdown(f"#### :material/lock: {escape(permisos_plan.mensaje_bloqueo(clave))}")
    # Dentro de una ventana el clic solo recarga la ventana; por eso, tras cambiar la vista, se relanza la app completa para dibujarla.
    if st.button("Ir al plan correspondiente", key="bloqueo_ir_planes", type="primary", width="stretch"):
        ir_a_planes("bloqueo")
        st.rerun()


# TITULO TEXTO DE PRECIO

def usd_texto(precio: float) -> str:
    """Precio en formato español, con coma decimal y sin «,00» si es redondo (4,99 · 15)."""
    texto = f"{float(precio):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return texto[:-3] if texto.endswith(",00") else texto


# TITULO PRECIO DEL PLAN

def _precio_plan(clave: str, variante: int) -> float:
    """Precio mensual (USD) del plan `clave` que corresponde a la `variante` del usuario (da la vuelta si el plan tiene menos variantes)."""
    precios = configuracion.PLANES_IA[clave].get("precios") or [0]
    return float(precios[variante % len(precios)])


# TITULO PRECIO DE

def precio_de(clave: str, usuario_id) -> float:
    """Precio mensual (USD) del plan `clave` que le corresponde al usuario (siempre la misma variante de precio para el mismo usuario)."""
    variantes = max(len(p.get("precios", [0])) for p in configuracion.PLANES_IA.values())
    return _precio_plan(clave, demanda.variante_de(usuario_id, variantes))


# TITULO COMPRAR CON BILLETERA

def comprar_con_billetera(clave: str, precio: float, variante: int, usuario_id, origen: str) -> None:
    """Callback de los botones «Comprar con billetera»: cobra el precio del plan del saldo virtual y pasa la cuenta a ese plan (origen «pago»).

    Deja en session_state el aviso de éxito o el error legible (saldo insuficiente, etc.) para que la vista lo muestre una vez. Registra el evento
    `plan_activado` con el origen `billetera`. No devuelve nada."""
    anterior = cuota_ia.plan_actual()
    try:
        restante = billetera.comprar_plan(clave, precio)
    except billetera.ErrorBilletera as e:
        st.session_state[_CLAVE_ERROR] = str(e)
        return
    demanda.registrar("plan_activado", usuario_id, clave, precio, variante, "billetera", anterior=anterior)
    nombre = configuracion.PLANES_IA[clave]["nombre"]
    st.session_state[_CLAVE_AVISO] = f"Compraste el plan {nombre} por {precio:,.2f} USD de tu billetera virtual (saldo: {restante:,.2f} USD).".replace(",", "X").replace(".", ",").replace("X", ".")


# TITULO USAR PLAN

def _usar_plan(clave: str, precio: float, variante: int, usuario_id, origen: str) -> None:
    """Callback de los botones «Contratar» y «Pasar al plan Gratis».

    El plan Gratis se activa al instante. Un plan de pago NO se activa (hasta que exista la pasarela de pago con Flow): solo se guarda el clic de interés y se deja anotado
    el plan para mostrar el agradecimiento y la encuesta. Con `configuracion.PLANES_LIBRES` (solo desarrollo) cualquier plan se activa sin pagar."""
    nombre_plan = configuracion.PLANES_IA[clave]["nombre"]
    if clave != "gratis" and not configuracion.PLANES_LIBRES:
        # Los planes de pago esperan la pasarela de pago (Flow): el clic solo deja registrado el interés y no cambia el plan
        demanda.registrar("clic_plan", usuario_id, clave, precio, variante, origen)
        st.session_state[_CLAVE_INTERES] = {"plan": clave, "precio": precio, "variante": variante, "origen": origen}
        st.session_state[_CLAVE_AVISO] = f"El pago del plan {nombre_plan} con Flow estará disponible muy pronto. Dejamos registrado tu interés."
        return
    anterior = cuota_ia.plan_actual()
    if cuota_ia.fijar_plan(clave, "prueba"):
        demanda.registrar("plan_activado", usuario_id, clave, precio, variante, origen, anterior=anterior)
        st.session_state[_CLAVE_AVISO] = (f"Ahora estás en el plan {configuracion.PLANES_IA[clave]['nombre']}." if not configuracion.PLANES_LIBRES else f"Ahora estás en el plan {configuracion.PLANES_IA[clave]['nombre']} (PLANES_LIBRES: sin pago, solo desarrollo). Los límites y funciones de la plataforma ya cambiaron.")
    else:
        st.session_state[_CLAVE_AVISO] = "No pudimos guardar el cambio de plan. Inténtalo de nuevo en un momento."
        return
    if clave != "gratis":
        demanda.registrar("clic_plan", usuario_id, clave, precio, variante, origen)
        st.session_state[_CLAVE_INTERES] = {"plan": clave, "precio": precio, "variante": variante, "origen": origen}
    else:
        st.session_state.pop(_CLAVE_INTERES, None)


# TITULO CELDA

def _celda(f: dict, valor) -> str:
    """Texto de una celda del cuadro comparativo: ✓ o — para las funciones de sí/no, la cantidad con puntos de miles, los perfiles con su nombre o el texto."""
    if isinstance(valor, bool):
        return "<span class='planes-si'>✓</span>" if valor else "<span class='planes-no'>—</span>"
    if isinstance(valor, (int, float)):
        return f"{valor:,.0f}".replace(",", ".") if valor else "<span class='planes-no'>—</span>"
    if isinstance(valor, list):
        return escape(", ".join(_TEXTOS["perfiles"].get(x, x) for x in valor))
    return escape(str(valor or "—"))


# TITULO TABLA COMPARATIVA

def _tabla_comparativa(plan_actual: str) -> str:
    """HTML del cuadro que compara todas las funciones de los cuatro planes, agrupadas por categoría. Resalta la columna del plan actual y marca con
    «pronto» las funciones que ya están definidas pero todavía no se aplican en la plataforma."""
    matriz = permisos_plan.matriz()
    claves = list(configuracion.PLANES_IA)
    cabecera = "".join(f"<th class='{'planes-col-actual' if c == plan_actual else ''}'>{escape(configuracion.PLANES_IA[c]['nombre'])}</th>" for c in claves)
    filas = []
    for cat in matriz["categorias"]:
        filas.append(f"<tr class='planes-cat'><td colspan='{len(claves) + 1}'>{escape(cat['nombre'])}</td></tr>")
        for f in (x for x in matriz["funciones"] if x["categoria"] == cat["clave"]):
            pronto = " <span class='planes-pronto'>pronto</span>" if f["estado"] != "aplicado" else ""
            unidad = f" <span class='planes-unidad'>({escape(f['unidad'])})</span>" if f.get("unidad") else ""
            celdas = "".join(f"<td class='{'planes-col-actual' if c == plan_actual else ''}'>{_celda(f, permisos_plan.valor(f['clave'], c))}</td>" for c in claves)
            filas.append(f"<tr><td title='{escape(f['descripcion'])}'>{escape(f['nombre'])}{unidad}{pronto}</td>{celdas}</tr>")
    return ("<div class='planes-comparar'><div class='planes-comparar-titulo'>Compara todas las funciones</div>"
            f"<table class='planes-tabla'><thead><tr><th>Función</th>{cabecera}</tr></thead><tbody>{''.join(filas)}</tbody></table>"
            "<div class='planes-pie'>«pronto» marca las funciones que ya están definidas para ese plan pero todavía no se aplican en la plataforma.</div></div>")


# TITULO FORMULARIO INTERES

def _formulario_interes(usuario: dict, interes: dict) -> None:
    """Agradecimiento y encuesta tras el clic: aclara que el pago con Flow llegará pronto, ofrece avisar al correo y pregunta precio justo y motivo."""
    plan = configuracion.PLANES_IA[interes["plan"]]["nombre"]
    st.html("<div class='planes-gracias'><b>Gracias por tu interés en el plan " + escape(plan) + ".</b> El pago con Flow estará disponible muy pronto y tu interés ya quedó "
            "registrado. Si quieres, responde estas dos preguntas y deja tu correo para que te avisemos cuando puedas contratarlo.</div>")
    with st.form("planes_encuesta"):
        precio_justo = st.selectbox("¿Qué precio mensual te parecería justo por este plan?", demanda.RANGOS_PRECIO, index=None, placeholder="Elige una opción")
        motivo = st.selectbox("¿Qué es lo que más te interesa del plan?", demanda.MOTIVOS, index=None, placeholder="Elige una opción")
        correo = usuario.get("email") or ""
        avisar = st.checkbox(f"Avísame cuando esté disponible{' (' + correo + ')' if correo else ''}", value=False,
                             help="Solo guardamos tu correo si marcas esta casilla.")
        enviar = st.form_submit_button("Enviar respuestas", type="primary")
    if enviar:
        uid = usuario.get("id")
        if precio_justo or motivo:
            demanda.registrar("encuesta", uid, interes["plan"], interes["precio"], interes["variante"], interes["origen"],
                              precio_justo=precio_justo or "", motivo=motivo or "")
        if avisar and correo:
            demanda.registrar("lista_espera", uid, interes["plan"], interes["precio"], interes["variante"], interes["origen"], correo=correo)
        st.success("¡Gracias! Tus respuestas quedaron registradas." + (" Te avisaremos cuando el plan esté disponible." if avisar and correo else ""))


# TITULO RENDERIZAR PANEL PLANES

def renderizar_panel_planes(main=None) -> None:
    """Dibuja la vista Planes: aviso de que el pago con Flow llegará pronto, las tarjetas de los planes y, tras un clic, el agradecimiento con la encuesta.

    `main` no se usa (se conserva por compatibilidad con las demás vistas). Registra una vista por visita (con su origen) y no devuelve nada."""
    st.html(_estaticos.estilos(_CSS) + vitrina_planes.estilos())
    usuario = st.session_state.get("usuario_informacion") or {}
    uid = usuario.get("id") if isinstance(usuario, dict) else None
    usuario = usuario if isinstance(usuario, dict) else {}
    origen, visita = st.session_state.get(_CLAVE_ORIGEN, ("menu", "inicio"))
    variantes = max(len(p.get("precios", [0])) for p in configuracion.PLANES_IA.values())
    variante = demanda.variante_de(uid, variantes)
    if st.session_state.get("planes_visita") != visita:        # una visita nueva: se anota una sola vez, aunque la página se redibuje
        st.session_state["planes_visita"] = visita
        demanda.registrar("vista_planes", uid, variante=variante, origen=origen)
    plan_actual = cuota_ia.plan_actual()
    estado_cuota = cuota_ia.estado()
    with st.container(key="planes_contenedor"):
        st.html("<div class='vp-cabecera'><span class='vp-etiqueta'>Planes</span><div class='vp-titulo'>Elige el plan que <span>impulsa tu trading</span></div>"
                "<p class='vp-sub'>Cada plan te da más preguntas al agente de IA por semana, más vigilancias automáticas y más herramientas. Cambia de plan cuando quieras.</p></div>"
                "<div class='planes-aviso'>" + ("Modo de desarrollo (PLANES_LIBRES): puedes cambiar a cualquier plan sin pagar, también «comprándolo» con el saldo virtual de tu Billetera."
                                              if configuracion.PLANES_LIBRES else
                                              "Los planes de pago se contratan en línea con Flow. El pago estará disponible muy pronto: deja tu interés en el plan que quieres y te avisamos.") + "</div>")
        aviso = st.session_state.pop(_CLAVE_AVISO, None)
        if aviso:
            st.success(aviso)
        error = st.session_state.pop(_CLAVE_ERROR, None)
        if error:
            st.error(error)
        columnas = st.columns(len(configuracion.PLANES_IA), gap="medium")
        for col, clave in zip(columnas, configuracion.PLANES_IA):
            precio = _precio_plan(clave, variante)
            es_actual = clave == plan_actual
            with col:
                # Tarjeta de la vitrina: cabecera (nombre, precio y preguntas), los botones reales del plan y la lista de lo que incluye
                with st.container(key=f"vpc_{clave}" + ("_actual" if es_actual else "")):
                    st.html(vitrina_planes.html_cabecera(clave, con_boton=False, precio=precio))
                    if es_actual:
                        st.button("Tu plan actual", key=f"plan_quiero_{clave}", icon=":material/check_circle:", width="stretch", disabled=True)
                        if estado_cuota.get("plan_vence"):
                            st.html(f"<div class='vp-vence'>Vigente hasta el {estado_cuota['plan_vence']}</div>")
                    elif clave == "gratis" and plan_actual != "gratis" and not configuracion.PLANES_LIBRES:
                        # Bajar a Gratis desde un plan de pago no tiene vuelta mientras no exista el pago con Flow (los planes de pago no se activan solos): se pide confirmar
                        with st.popover("Pasar al plan Gratis", width="stretch"):
                            st.warning(f"Vas a dejar el plan {configuracion.PLANES_IA[plan_actual]['nombre']}. Hasta que esté disponible el pago con Flow no podrás volver a "
                                       "contratarlo por tu cuenta.")
                            st.button("Sí, pasar a Gratis", key=f"plan_confirmar_{clave}", type="primary", width="stretch", on_click=_usar_plan,
                                      args=(clave, precio, variante, uid, origen))
                    else:
                        st.button(("Usar este plan" if configuracion.PLANES_LIBRES else "Contratar") if clave != "gratis" else "Pasar al plan Gratis", key=f"plan_quiero_{clave}",
                                  icon=":material/workspace_premium:" if clave != "gratis" else None,
                                  type="primary" if clave != "gratis" else "secondary", width="stretch", on_click=_usar_plan,
                                  args=(clave, precio, variante, uid, origen))
                        if clave != "gratis" and configuracion.PLANES_LIBRES:
                            st.button("Comprar con billetera", key=f"plan_comprar_{clave}", icon=":material/account_balance_wallet:",
                                      width="stretch", on_click=comprar_con_billetera, args=(clave, precio, variante, uid, origen))
                    st.html(vitrina_planes.html_lista(clave))
        st.html(vitrina_planes.html_comun())
        interes = st.session_state.get(_CLAVE_INTERES)
        if interes:
            _formulario_interes(usuario, interes)
        st.html(_tabla_comparativa(plan_actual))


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara panel .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
