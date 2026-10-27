# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara secciones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Formularios de cada sección del perfil: datos personales, documento, contacto, inversor, preferencias, seguridad y cuenta.

Las secciones con campos (datos.json) se dibujan con un formulario genérico que valida y guarda con `almacen`; Seguridad
(cambio de contraseña) y Cuenta de trading (datos de solo lectura) tienen su propio dibujo. Lo llama panel.py.
"""
from datetime import date
from typing import Any

import streamlit as st

from componentes_plataforma.agente_paneles.formato import escapar_html
from componentes_plataforma.perfil import almacen
from componentes_plataforma.perfil.datos import PREFIJOS, opciones, seccion as _seccion
from componentes_plataforma.perfil.validacion import (mascara, validar_contrasena_nueva, validar_documento,
                                                       validar_apodo, validar_nacimiento, validar_telefono)
from herramientas import gestor_autenticacion
from herramientas.puente_mt5 import NOMBRE_BROKER, obtener_info_cuenta

# Clave de session_state con el aviso (tipo, texto) que se muestra tras guardar y recargar la vista.
CLAVE_AVISO = "perfil_aviso"
# Rango de fechas que acepta el selector de fecha de nacimiento y el de vencimiento del documento.
_NACIMIENTO_MIN, _VENCIMIENTO_MAX = date(1900, 1, 1), date(2100, 12, 31)


# TITULO USUARIO ID

def _usuario_id(usuario: dict[str, Any]) -> Any:
    """Id del usuario (el de la tabla `usuarios`); "local" si no hay sesión, para el modo de desarrollo."""
    return usuario.get("id") or "local"


# TITULO FECHA DE

def _fecha_de(valor: Any) -> date | None:
    """Convierte el valor guardado (texto AAAA-MM-DD o fecha) a `date`; None si no hay valor o no se entiende."""
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor)[:10]) if valor else None
    except ValueError:
        return None


# TITULO SELECTOR

def _selector(campo: dict[str, Any], perfil: dict[str, Any], clave: str) -> Any:
    """Dibuja una lista desplegable con las opciones del campo y devuelve el id elegido (None si no se eligió nada)."""
    ops = opciones(campo["opciones"])
    ids = [i for i, _ in ops]
    actual = perfil.get(campo["id"]) or campo.get("defecto")     # lo guardado y, si no hay nada, el valor por defecto del campo
    return st.selectbox(campo["etiqueta"], ids, index=ids.index(actual) if actual in ids else None,
                        format_func=dict(ops).get, placeholder="Selecciona…", key=clave, help=campo.get("ayuda"))


# TITULO DIBUJAR CAMPO

def _dibujar_campo(campo: dict[str, Any], perfil: dict[str, Any], valores: dict[str, Any]) -> None:
    """Dibuja el control de un campo según su tipo y deja el valor ingresado en `valores[id]`.

    Tipos: texto, select, fecha, multi (varias opciones), bool, documento (número enmascarado: vacío conserva el guardado),
    telefono (prefijo + número) y notificaciones (un interruptor por aviso)."""
    id_, tipo = campo["id"], campo["tipo"]
    clave = f"perfil_{id_}"
    if tipo == "texto":
        valores[id_] = st.text_input(campo["etiqueta"], value=perfil.get(id_) or "", max_chars=campo.get("max"), key=clave,
                                     help=campo.get("ayuda")).strip()
    elif tipo == "select":
        valores[id_] = _selector(campo, perfil, clave)
    elif tipo == "fecha":
        minimo = _NACIMIENTO_MIN if id_ == "fecha_nacimiento" else date(2000, 1, 1)
        maximo = date.today() if id_ == "fecha_nacimiento" else _VENCIMIENTO_MAX
        valores[id_] = st.date_input(campo["etiqueta"], value=_fecha_de(perfil.get(id_)), min_value=minimo, max_value=maximo,
                                     format="DD/MM/YYYY", key=clave, help=campo.get("ayuda"))
    elif tipo == "multi":
        ops = opciones(campo["opciones"])
        valores[id_] = st.multiselect(campo["etiqueta"], [i for i, _ in ops], default=[x for x in (perfil.get(id_) or [])
                                      if x in dict(ops)], format_func=dict(ops).get, placeholder="Selecciona…", key=clave)
    elif tipo == "bool":
        valores[id_] = st.checkbox(campo["etiqueta"], value=bool(perfil.get(id_)), key=clave)
    elif tipo == "documento":
        guardado = perfil.get(id_)
        valores[id_] = st.text_input(campo["etiqueta"], value="", max_chars=campo.get("max"), key=clave,
                                     placeholder="Ingresa el número" if not guardado else "Guardado: " + mascara(guardado)).strip()
        if guardado:
            st.caption(f"Documento guardado: {mascara(guardado)} · déjalo vacío para conservarlo.")
    elif tipo == "telefono":
        c1, c2 = st.columns([1, 2])
        prefijos = sorted({p for p in PREFIJOS.values() if p != "+"}, key=lambda p: (p != "+56", p))
        guardado = perfil.get("telefono_prefijo") or "+56"
        with c1:
            valores["telefono_prefijo"] = st.selectbox("Prefijo", prefijos, index=prefijos.index(guardado) if guardado in prefijos else 0,
                                                       key="perfil_telefono_prefijo")
        with c2:
            valores[id_] = st.text_input(campo["etiqueta"], value=perfil.get(id_) or "", max_chars=14, key=clave,
                                         help=campo.get("ayuda"), placeholder="987654321").strip()
    elif tipo == "notificaciones":
        st.markdown("**Notificaciones**")
        previo = perfil.get(id_) or {}
        valores[id_] = {n["id"]: st.toggle(n["nombre"], value=bool(previo.get(n["id"], True)), key=f"perfil_notif_{n['id']}",
                                           help=n.get("ayuda")) for n in _opciones_notificaciones()}


# TITULO OPCIONES NOTIFICACIONES

def _opciones_notificaciones() -> list[dict[str, Any]]:
    """Avisos que se pueden activar o desactivar, con su nombre y ayuda (datos.json, clave `notificaciones`)."""
    from componentes_plataforma.perfil.datos import _D
    return _D["notificaciones"]


# TITULO VALIDAR

def _validar(seccion: dict[str, Any], valores: dict[str, Any], perfil: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Valida lo ingresado en una sección y devuelve (errores, valores normalizados listos para guardar).

    Revisa campos requeridos, mayoría de edad, apodo, documento (con RUT módulo 11) y teléfonos. En el documento, un valor vacío
    conserva el guardado salvo que haya cambiado el tipo de documento."""
    errores: list[str] = []
    salida = dict(valores)
    for c in seccion["campos"]:
        v = valores.get(c["id"])
        if c.get("requerido") and c["tipo"] not in ("documento", "telefono", "fecha") and v in (None, "", []):
            errores.append(f"Completa «{c['etiqueta']}».")
        if c["tipo"] == "texto" and isinstance(v, str) and ("<" in v or ">" in v):
            errores.append(f"«{c['etiqueta']}» no puede llevar los caracteres < ni >.")
    if "fecha_nacimiento" in valores:
        ok, msg = validar_nacimiento(valores["fecha_nacimiento"])
        if not ok:
            errores.append(msg)
    if "tipo_documento" in valores:
        numero = valores.get("numero_documento") or ""
        if not numero and perfil.get("numero_documento") and valores.get("tipo_documento") == perfil.get("tipo_documento"):
            salida.pop("numero_documento", None)        # vacío = conservar el número guardado
        else:
            ok, msg, normal = validar_documento(valores.get("tipo_documento") or "", numero)
            errores.append(msg) if not ok else salida.__setitem__("numero_documento", normal)
    if "apodo" in valores:
        ok, msg, normal = validar_apodo(valores["apodo"])
        errores.append(msg) if not ok else salida.__setitem__("apodo", normal)
    if "telefono_movil" in valores:
        ok, msg, normal = validar_telefono(valores["telefono_movil"])
        errores.append(msg) if not ok else salida.__setitem__("telefono_movil", normal)
    if "telefono_alterno" in valores:
        ok, msg, normal = validar_telefono(valores["telefono_alterno"], opcional=True)
        errores.append(msg) if not ok else salida.__setitem__("telefono_alterno", normal)
    return errores, salida


# TITULO FORMULARIO

def _formulario(seccion: dict[str, Any], usuario: dict[str, Any], perfil: dict[str, Any]) -> None:
    """Dibuja el formulario genérico de una sección y, al guardar, valida, escribe en el almacén y recarga la vista.

    Si cambian nombres o apellidos actualiza también el nombre que se muestra (tabla `usuarios` y sesión)."""
    valores: dict[str, Any] = {}
    with st.form(f"perfil_form_{seccion['id']}", border=False):
        campos = seccion["campos"]
        i = 0
        while i < len(campos):
            c = campos[i]
            ancho = c["tipo"] in ("telefono", "notificaciones", "multi", "bool") or c["id"] in ("direccion",)
            if ancho:
                _dibujar_campo(c, perfil, valores)
                i += 1
            else:
                izq, der = st.columns(2)
                with izq:
                    _dibujar_campo(c, perfil, valores)
                sig = campos[i + 1] if i + 1 < len(campos) else None
                if sig and sig["tipo"] not in ("telefono", "notificaciones", "multi", "bool") and sig["id"] != "direccion":
                    with der:
                        _dibujar_campo(sig, perfil, valores)
                    i += 2
                else:
                    i += 1
        if seccion["id"] == "preferencias":
            st.caption("Estas preferencias se guardan en tu perfil; la plataforma las irá aplicando en próximas versiones.")
        guardar = st.form_submit_button("Guardar cambios", type="primary", icon=":material/save:")
    if not guardar:
        return
    errores, datos = _validar(seccion, valores, perfil)
    if errores:
        for e in errores:
            st.error(e)
        return
    resultado = almacen.guardar(_usuario_id(usuario), datos)
    if not resultado["ok"]:
        st.error(resultado["mensaje"])
        return
    if "nombres" in datos and "apellidos" in datos:
        completo = f"{datos['nombres']} {datos['apellidos']}".strip()
        if almacen.modo() == "supabase":
            gestor_autenticacion.actualizar_nombre(usuario.get("id"), completo)
        usuario["nombre"] = completo       # el mismo diccionario vive en el almacén de sesiones: no se pierde con F5
    st.session_state[CLAVE_AVISO] = ("ok", resultado["mensaje"])
    st.rerun()


# TITULO SEGURIDAD

def _seguridad(usuario: dict[str, Any]) -> None:
    """Sección Seguridad: correo (solo lectura), cambio de contraseña, autenticación en dos pasos (próximamente) y cerrar sesión."""
    st.text_input("Correo electrónico", value=usuario.get("email", ""), disabled=True, key="perfil_email_solo_lectura",
                  help="El correo es tu identificador de acceso y no se puede cambiar desde aquí.")
    st.markdown("**Cambiar contraseña**")
    with st.form("perfil_form_contrasena", border=False):
        actual = st.text_input("Contraseña actual", type="password", key="perfil_pw_actual")
        c1, c2 = st.columns(2)
        with c1:
            nueva = st.text_input("Contraseña nueva", type="password", key="perfil_pw_nueva", help="Mínimo 8 caracteres, con letras y números.")
        with c2:
            repetida = st.text_input("Repite la contraseña nueva", type="password", key="perfil_pw_repetida")
        enviar = st.form_submit_button("Actualizar contraseña", type="primary", icon=":material/key:")
    if enviar:
        ok, msg = validar_contrasena_nueva(actual, nueva, repetida)
        if not ok:
            st.error(msg)
        else:
            r = gestor_autenticacion.cambiar_contrasena(usuario.get("id"), actual, nueva)
            (st.success if r["ok"] else st.error)(r["mensaje"])
    st.markdown("**Autenticación en dos pasos**")
    st.toggle("Pedir un código adicional al iniciar sesión", value=False, disabled=True, key="perfil_2fa",
              help="Próximamente.")
    st.caption("Próximamente: protegerás tu cuenta con un código de una aplicación de autenticación.")
    st.html("<a class='perfil-salir' href='?logout=1' target='_self'>Cerrar sesión en este dispositivo</a>")


# TITULO CUENTA

def _cuenta(usuario: dict[str, Any]) -> None:
    """Sección Cuenta de trading: datos de solo lectura de la cuenta del bróker y de las autorizaciones aceptadas."""
    info = obtener_info_cuenta() or {}
    ok = bool(info) and "error" not in info
    moneda = info.get("currency", "USD") if ok else "—"
    celdas = [
        ("Bróker", NOMBRE_BROKER),
        ("Tipo de cuenta", ("Demo" if str(info.get("tipo", "")).lower() == "demo" else str(info.get("tipo", "—"))) if ok else "Sin conexión"),
        ("Moneda", moneda),
        ("Saldo", f"{info.get('balance', 0):,.2f} {moneda}" if ok else "—"),
        ("Equity", f"{info.get('equity', 0):,.2f} {moneda}" if ok else "—"),
        ("Margen libre", f"{info.get('margin_free', 0):,.2f} {moneda}" if ok else "—"),
    ]
    st.html("<div class='perfil-cuadricula'>" + "".join(
        f"<div class='perfil-dato'><span>{escapar_html(k)}</span><b>{escapar_html(v)}</b></div>" for k, v in celdas) + "</div>")
    st.markdown("**Autorizaciones aceptadas**")
    filas: list[str] = []
    try:
        from componentes_plataforma.operacion_un_clic.registro import _leer as _leer_un_clic
        a = _leer_un_clic().get(str(_usuario_id(usuario)))
        if a:
            filas.append(f"One-Click Trading · aceptado el {escapar_html(str(a.get('fecha', ''))[:10])}")
    except Exception:  # noqa: BLE001 - el registro es opcional
        pass
    try:
        from componentes_plataforma.vigilancia_terminos.registro import aceptaciones_de
        for a in aceptaciones_de(str(_usuario_id(usuario)))[-5:]:
            filas.append(f"Vigilancia automática de {escapar_html(a.get('simbolo'))} · aceptada el {escapar_html(str(a.get('fecha', ''))[:10])}")
    except Exception:  # noqa: BLE001
        pass
    st.html("".join(f"<div class='perfil-fila'>{f}</div>" for f in filas) or "<div class='perfil-vacio'>Aún no has aceptado ninguna autorización.</div>")


# TITULO DIBUJAR

def dibujar(id_seccion: str, usuario: dict[str, Any], perfil: dict[str, Any]) -> None:
    """Dibuja la sección `id_seccion`: su título y descripción, el aviso pendiente de la acción anterior y su contenido."""
    s = _seccion(id_seccion)
    st.html(f"<div class='perfil-seccion-titulo'>{escapar_html(s['titulo'])}</div>"
            f"<div class='perfil-seccion-desc'>{escapar_html(s['descripcion'])}</div>")
    aviso = st.session_state.pop(CLAVE_AVISO, None)
    if aviso:
        (st.success if aviso[0] == "ok" else st.error)(aviso[1])
    if perfil.get("_error"):
        st.warning(perfil["_error"])
    if id_seccion == "seguridad":
        _seguridad(usuario)
    elif id_seccion == "cuenta":
        _cuenta(usuario)
    else:
        _formulario(s, usuario, perfil)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara secciones .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
