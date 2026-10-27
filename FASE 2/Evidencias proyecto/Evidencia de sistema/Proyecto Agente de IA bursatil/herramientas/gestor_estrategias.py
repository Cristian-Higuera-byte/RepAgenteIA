# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara gestor_estrategias .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""Gestión de las estrategias de copy trading por parte de su gestor: requisitos, creación, edición, publicación y seguidores.

Todo se guarda en Supabase (tablas `estrategias`, `copias`, `comisiones_rendimiento`; esquema en `herramientas/sql/copytrading.sql`) y se lee con el cliente
de `gestor_autenticacion`. Las reglas están en `configuracion.COPYTRADING`.

Para publicar una estrategia el gestor debe cumplir TODO esto: tener apodo en su perfil (es su nombre público), estar en una cuenta demo (por ahora el copy
trading es solo demo), tener registrados al menos `dias_minimos` días de historial y `operaciones_minimas` operaciones cerradas, aceptar compartir su historial y no
superar `max_estrategias` estrategias vigentes. Un borrador se puede guardar sin cumplirlo.

Estados de una estrategia: borrador → publicada ⇄ pausada → cerrada. Una pausada no admite copias nuevas y no sale en el listado; una cerrada no vuelve. Si la
estrategia tiene copias activas o pausadas, no se puede cerrar ni cambiar su comisión ni su inversión mínima (las copias existentes se hicieron con esas condiciones).
Las funciones públicas lanzan `ErrorGestor` con un mensaje legible cuando algo no se puede hacer.
"""
import re
from datetime import datetime, timezone

import configuracion
from herramientas import gestor_autenticacion, metricas_estrategia
from herramientas.backends import sesiones_capital

_TABLA = "estrategias"
# Estados en los que una estrategia cuenta como vigente (ocupa uno de los cupos del gestor)
_VIGENTES = ("borrador", "publicada", "pausada")
# Transiciones de estado permitidas: estado actual -> estados a los que puede pasar
_TRANSICIONES = {"borrador": ("publicada", "cerrada"), "publicada": ("pausada", "cerrada"), "pausada": ("publicada", "cerrada")}
_TIPOS = ("manual", "algoritmico")


# TITULO ERROR GESTOR

class ErrorGestor(Exception):
    """Se lanza cuando una acción del gestor no se puede hacer (requisito sin cumplir, dato inválido, estado que no lo permite o sin conexión). El mensaje es legible."""


# TITULO CLIENTE

def _cliente():
    """Cliente de Supabase, o `ErrorGestor` si no está configurado."""
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        raise ErrorGestor("El área de gestor necesita la base de datos (Supabase), que no está configurada en este equipo.")
    return cliente


# TITULO DISPONIBLE

def disponible() -> bool:
    """True si el área de gestor se puede usar (hay Supabase configurado)."""
    return gestor_autenticacion._supabase is not None


# TITULO CUENTA ACTUAL

def cuenta_actual() -> str:
    """Tipo de cuenta en uso: "demo" o "real". En el modo de un solo usuario (cuenta del .env) se considera demo."""
    clave = sesiones_capital.clave_actual()
    return ("demo" if clave[1] else "real") if len(clave) == 2 else "demo"


# TITULO AHORA

def _ahora() -> str:
    """Fecha y hora actual en UTC como texto ISO."""
    return datetime.now(timezone.utc).isoformat()


# TITULO REQUISITOS

def requisitos(usuario_id, cuenta: str | None = None) -> dict:
    """Comprueba qué requisitos para publicar cumple el usuario.

    Devuelve {"items": [{"clave", "texto", "ok", "detalle"}], "cumple": bool, "apodo": texto o None, "vigentes": estrategias vigentes}. Los ítems son: apodo, cuenta demo,
    días de historial, operaciones cerradas y cupo de estrategias."""
    cliente, cfg, cuenta = _cliente(), configuracion.COPYTRADING, cuenta or cuenta_actual()
    perfil = (cliente.table("perfiles_usuario").select("apodo").eq("usuario_id", int(usuario_id)).limit(1).execute().data or [{}])[0]
    apodo = (perfil.get("apodo") or "").strip() or None
    primera = (cliente.table("operaciones").select("abierta_en").eq("usuario_id", int(usuario_id)).eq("cuenta_tipo", cuenta).order("abierta_en").limit(1).execute().data or [None])[0]
    dias = max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(str(primera["abierta_en"]).replace("Z", "+00:00"))).days) if primera else 0
    cerradas = len(cliente.table("operaciones").select("id").eq("usuario_id", int(usuario_id)).eq("cuenta_tipo", cuenta).eq("estado", "cerrada")
                   .limit(int(cfg["operaciones_minimas"])).execute().data or [])
    vigentes = len(cliente.table(_TABLA).select("id").eq("gestor_id", int(usuario_id)).in_("estado", list(_VIGENTES)).execute().data or [])
    items = [
        {"clave": "apodo", "texto": "Tener un apodo en tu perfil (es tu nombre público)", "ok": bool(apodo), "detalle": f"@{apodo}" if apodo else "Agrégalo en Mi perfil > Datos personales"},
        {"clave": "cuenta", "texto": "Usar la cuenta demo (por ahora el copy trading es solo demo)", "ok": cuenta == "demo", "detalle": "Cuenta " + cuenta},
        {"clave": "dias", "texto": f"Al menos {cfg['dias_minimos']} días de historial registrado", "ok": dias >= cfg["dias_minimos"], "detalle": f"{dias} días"},
        {"clave": "operaciones", "texto": f"Al menos {cfg['operaciones_minimas']} operaciones cerradas", "ok": cerradas >= cfg["operaciones_minimas"], "detalle": f"{cerradas} cerradas" if cerradas < cfg["operaciones_minimas"] else f"{cerradas} o más"},
        {"clave": "cupo", "texto": f"Máximo {cfg['max_estrategias']} estrategias vigentes", "ok": vigentes < cfg["max_estrategias"], "detalle": f"{vigentes} vigentes"},
    ]
    return {"items": items, "cumple": all(i["ok"] for i in items), "apodo": apodo, "vigentes": vigentes}


# TITULO VALIDAR

def validar(datos: dict) -> dict:
    """Valida y normaliza los datos de una estrategia: nombre, tipo, categoría, biografía, descripción, comisión e inversión mínima.

    Devuelve el diccionario listo para guardar o lanza `ErrorGestor` con el primer problema encontrado."""
    cfg = configuracion.COPYTRADING
    nombre = re.sub(r"\s+", " ", str(datos.get("nombre") or "")).strip()
    if not 3 <= len(nombre) <= 40:
        raise ErrorGestor("El nombre debe tener entre 3 y 40 caracteres.")
    if not re.fullmatch(r"[\w .&()'-]+", nombre):
        raise ErrorGestor("El nombre solo puede llevar letras, números, espacios y . & ( ) ' -")
    tipo = datos.get("tipo") or "manual"
    if tipo not in _TIPOS:
        raise ErrorGestor("El tipo de estrategia no es válido.")
    categoria = datos.get("categoria") or None
    if categoria is not None and categoria not in cfg["categorias"]:
        raise ErrorGestor("La categoría no es válida.")
    biografia, descripcion = str(datos.get("biografia") or "").strip(), str(datos.get("descripcion") or "").strip()
    if len(biografia) > 500 or len(descripcion) > 1000:
        raise ErrorGestor("La biografía admite hasta 500 caracteres y la descripción hasta 1.000.")
    if any(c in texto for texto in (biografia, descripcion) for c in "<>"):
        raise ErrorGestor("Los textos no pueden llevar los caracteres < ni >.")
    try:
        comision = round(float(datos.get("comision_pct", cfg["comision_defecto"])), 2)
        minimo = round(float(datos.get("inversion_minima", cfg["inversion_minima"])), 2)
    except (TypeError, ValueError):
        raise ErrorGestor("La comisión y la inversión mínima deben ser números.") from None
    if not 0 <= comision <= cfg["comision_max"]:
        raise ErrorGestor(f"La comisión debe estar entre 0 y {cfg['comision_max']:g} %.")
    if not cfg["inversion_minima"] <= minimo <= 100000:
        raise ErrorGestor(f"La inversión mínima debe estar entre {cfg['inversion_minima']:g} y 100.000 USD.")
    return {"nombre": nombre, "tipo": tipo, "categoria": categoria, "biografia": biografia, "descripcion": descripcion, "comision_pct": comision, "inversion_minima": minimo}


# TITULO COPIAS VIGENTES

def _copias_vigentes(cliente, estrategia_id) -> int:
    """Cantidad de copias activas o pausadas de una estrategia."""
    return len(cliente.table("copias").select("id").eq("estrategia_id", estrategia_id).in_("estado", ["activa", "pausada"]).execute().data or [])


# TITULO ESTRATEGIA PROPIA

def _propia(cliente, usuario_id, estrategia_id) -> dict:
    """Fila de la estrategia si es del usuario; `ErrorGestor` si no existe o es de otro."""
    fila = (cliente.table(_TABLA).select("*").eq("id", int(estrategia_id)).eq("gestor_id", int(usuario_id)).limit(1).execute().data or [None])[0]
    if not fila:
        raise ErrorGestor("No encontramos esa estrategia.")
    return fila


# TITULO NOMBRE REPETIDO

def _nombre_repetido(cliente, usuario_id, nombre: str, excepto=None) -> bool:
    """True si el gestor ya tiene otra estrategia con ese nombre (sin distinguir mayúsculas)."""
    filas = cliente.table(_TABLA).select("id,nombre").eq("gestor_id", int(usuario_id)).execute().data or []
    return any(f["nombre"].lower() == nombre.lower() and f["id"] != excepto for f in filas)


# TITULO GUARDAR ERROR

def _error_guardado(e: Exception) -> ErrorGestor:
    """Traduce un error de Supabase al mensaje que se muestra (nombre repetido u otro fallo)."""
    texto = str(e).lower()
    return ErrorGestor("Ya tienes una estrategia con ese nombre." if "duplicate" in texto or "unique" in texto else "No se pudo guardar la estrategia. Inténtalo de nuevo.")


# TITULO CREAR

def crear(usuario_id, datos: dict, publicar: bool = False) -> dict:
    """Crea una estrategia del gestor como borrador o ya publicada, y devuelve su fila.

    Para publicar exige cumplir todos los requisitos y que `datos["acepto_compartir"]` sea verdadero; el borrador solo exige que quepa en el cupo y que los datos sean
    válidos. La estrategia se guarda con la cuenta actual. Lanza `ErrorGestor` si algo no se cumple."""
    cliente, cuenta = _cliente(), cuenta_actual()
    limpio = validar(datos)
    req = requisitos(usuario_id, cuenta)
    if not next(i for i in req["items"] if i["clave"] == "cupo")["ok"]:
        raise ErrorGestor(f"Ya tienes {configuracion.COPYTRADING['max_estrategias']} estrategias vigentes. Cierra una para crear otra.")
    if _nombre_repetido(cliente, usuario_id, limpio["nombre"]):
        raise ErrorGestor("Ya tienes una estrategia con ese nombre.")
    fila = {"gestor_id": int(usuario_id), "cuenta_tipo": cuenta, **limpio, "estado": "borrador"}
    if publicar:
        _exigir_publicar(req, datos.get("acepto_compartir"))
        fila.update({"estado": "publicada", "acepto_compartir_en": _ahora(), "publicada_en": _ahora()})
    try:
        guardada = (cliente.table(_TABLA).insert(fila).execute().data or [fila])[0]
    except Exception as e:  # noqa: BLE001
        raise _error_guardado(e) from None
    if guardada.get("estado") == "publicada" and guardada.get("id"):
        metricas_estrategia.refrescar_en_segundo_plano(cliente, [guardada], {})
    return guardada


# TITULO EXIGIR PUBLICAR

def _exigir_publicar(req: dict, acepto) -> None:
    """Lanza `ErrorGestor` si falta algún requisito para publicar o el consentimiento para compartir el historial."""
    faltan = [i["texto"] for i in req["items"] if i["clave"] != "cupo" and not i["ok"]]
    if faltan:
        raise ErrorGestor("Todavía no puedes publicar: te falta " + "; ".join(t[0].lower() + t[1:] for t in faltan) + ".")
    if not acepto:
        raise ErrorGestor("Para publicar tienes que aceptar compartir tu historial de operaciones.")


# TITULO ACTUALIZAR

def actualizar(usuario_id, estrategia_id, datos: dict) -> dict:
    """Edita una estrategia propia (no cerrada) y devuelve la fila. La comisión y la inversión mínima no se pueden cambiar si ya tiene copias vigentes."""
    cliente = _cliente()
    actual = _propia(cliente, usuario_id, estrategia_id)
    if actual["estado"] == "cerrada":
        raise ErrorGestor("Una estrategia cerrada ya no se puede editar.")
    limpio = validar({**actual, **datos})
    if _nombre_repetido(cliente, usuario_id, limpio["nombre"], excepto=actual["id"]):
        raise ErrorGestor("Ya tienes una estrategia con ese nombre.")
    if _copias_vigentes(cliente, actual["id"]) and (float(limpio["comision_pct"]) != float(actual["comision_pct"]) or float(limpio["inversion_minima"]) != float(actual["inversion_minima"])):
        raise ErrorGestor("Con inversores activos no se puede cambiar la comisión ni la inversión mínima.")
    try:
        cliente.table(_TABLA).update({**limpio, "actualizada_en": _ahora()}).eq("id", actual["id"]).eq("gestor_id", int(usuario_id)).execute()
    except Exception as e:  # noqa: BLE001
        raise _error_guardado(e) from None
    return {**actual, **limpio}


# TITULO CAMBIAR ESTADO

def cambiar_estado(usuario_id, estrategia_id, nuevo: str, acepto_compartir: bool = False) -> dict:
    """Pasa una estrategia propia a otro estado (ver las transiciones permitidas en el encabezado) y devuelve la fila.

    Publicar un borrador exige cumplir los requisitos y aceptar compartir el historial; cerrar exige que no haya copias vigentes."""
    cliente = _cliente()
    actual = _propia(cliente, usuario_id, estrategia_id)
    if nuevo not in _TRANSICIONES.get(actual["estado"], ()):
        raise ErrorGestor(f"Una estrategia {actual['estado']} no puede pasar a {nuevo}.")
    cambios = {"estado": nuevo, "actualizada_en": _ahora()}
    if nuevo == "publicada" and actual["estado"] == "borrador":
        _exigir_publicar(requisitos(usuario_id, actual.get("cuenta_tipo", "demo")), acepto_compartir)
        cambios.update({"acepto_compartir_en": _ahora(), "publicada_en": _ahora()})
    if nuevo == "cerrada" and _copias_vigentes(cliente, actual["id"]):
        raise ErrorGestor("No puedes cerrar una estrategia con inversores activos.")
    cliente.table(_TABLA).update(cambios).eq("id", actual["id"]).eq("gestor_id", int(usuario_id)).execute()
    fila = {**actual, **cambios}
    if nuevo == "publicada":
        metricas_estrategia.refrescar_en_segundo_plano(cliente, [fila], {})
    return fila


# TITULO MIS ESTRATEGIAS

def mis_estrategias(usuario_id) -> list:
    """Estrategias del gestor (las más nuevas primero), cada una con `metricas` (fila de estrategias_metricas o {}), `copias` (activas o pausadas), `ganado` (comisiones ya cobradas) y `por_cobrar` (liquidadas pero sin cobrar)."""
    cliente = _cliente()
    filas = cliente.table(_TABLA).select("*").eq("gestor_id", int(usuario_id)).order("id", desc=True).execute().data or []
    if not filas:
        return []
    ids = [f["id"] for f in filas]
    metricas = {m["estrategia_id"]: m for m in (cliente.table("estrategias_metricas").select("*").in_("estrategia_id", ids).execute().data or [])}
    todas = cliente.table("copias").select("id,estrategia_id,estado").in_("estrategia_id", ids).execute().data or []
    copias = [c for c in todas if c["estado"] in ("activa", "pausada")]
    por_copia = {c["id"]: c["estrategia_id"] for c in todas}
    ganado: dict = {}
    por_cobrar: dict = {}
    if por_copia:
        for c in cliente.table("comisiones_rendimiento").select("copia_id,comision,movimiento_billetera_id").in_("copia_id", list(por_copia)).execute().data or []:
            destino = ganado if c.get("movimiento_billetera_id") is not None else por_cobrar
            destino[por_copia[c["copia_id"]]] = destino.get(por_copia[c["copia_id"]], 0.0) + float(c["comision"])
    return [{**f, "metricas": metricas.get(f["id"], {}), "copias": sum(1 for c in copias if c["estrategia_id"] == f["id"]),
             "ganado": round(ganado.get(f["id"], 0.0), 2), "por_cobrar": round(por_cobrar.get(f["id"], 0.0), 2)} for f in filas]


# TITULO SEGUIDORES

def seguidores(usuario_id, estrategia_id) -> list:
    """Copias de una estrategia propia, las más nuevas primero: [{"inversor": apodo o «Inversor n», "importe", "modo", "multiplicador", "estado", "desde"}].

    Solo se muestra el apodo del inversor, nunca sus datos personales."""
    cliente = _cliente()
    _propia(cliente, usuario_id, estrategia_id)
    copias = cliente.table("copias").select("*").eq("estrategia_id", int(estrategia_id)).order("id", desc=True).execute().data or []
    if not copias:
        return []
    ids = list({c["inversor_id"] for c in copias})
    apodos = {p["usuario_id"]: p.get("apodo") for p in (cliente.table("perfiles_usuario").select("usuario_id,apodo").in_("usuario_id", ids).execute().data or [])}
    return [{"inversor": ("@" + apodos[c["inversor_id"]]) if apodos.get(c["inversor_id"]) else f"Inversor {i}", "importe": c.get("importe"), "modo": c.get("modo"),
             "multiplicador": c.get("multiplicador"), "estado": c.get("estado"), "desde": c.get("creada_en")} for i, c in enumerate(copias, 1)]



# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara gestor_estrategias .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
