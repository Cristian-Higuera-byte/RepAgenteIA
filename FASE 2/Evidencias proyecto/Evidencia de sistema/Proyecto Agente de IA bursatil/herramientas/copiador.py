# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara copiador .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Motor del copy trading: abre la cuenta de inversor, crea las copias y replica las operaciones del gestor en la cuenta del seguidor.

Qué hace, en orden:
  1. `abrir_cuenta_inversor` registra al usuario como inversor (acepta los términos) y `crear_copia` crea la copia de una estrategia publicada con su modo de
     asignación (por importe invertido o por multiplicador fijo), si copia también las operaciones que el gestor ya tiene abiertas y su take profit y stop loss.
  2. Un motor en segundo plano (`iniciar_motor`, que se arranca junto con el de vigilancias y solo corre en modo multiusuario) revisa cada pocos segundos las copias vigentes y, para cada una,
     en la cuenta DEMO de su dueño: abre las operaciones nuevas del gestor, cierra las que el gestor cerró y vigila el take profit y el stop loss de la copia.
  3. Cada operación del gestor se replica UNA sola vez por copia (clave única en `copias_operaciones`), y el motor reclama la fila antes de enviar la orden: si algo
     se interrumpe, la fila queda «pendiente» y pasado `pendiente_vence_s` se marca «fallida» sin reintentar, para no duplicar nunca una orden.

Reglas de réplica:
  - Tamaño: por importe, volumen del gestor × (importe ÷ equity del gestor al abrir); por multiplicador, volumen del gestor × multiplicador. Se redondea hacia abajo al
    paso del instrumento; si queda bajo el mínimo del bróker la operación no se copia y se anota el motivo. El stop loss y el take profit del gestor se copian tal cual.
  - Solo se copian operaciones del gestor que él abrió (no las que a su vez eran copias de otro), y nadie puede copiar su propia estrategia.
  - Una copia pausada no abre operaciones nuevas pero sí cierra las que el gestor cierre; una cerrada solo cierra sus posiciones si se pidió así y liquida su comisión final.
  - Take profit y stop loss de la copia: porcentaje del importe invertido; al alcanzarlo se cierran las posiciones de la copia y la copia queda cerrada.
Límites conocidos: la copia depende de que el gestor tenga la plataforma abierta (sus operaciones se registran desde su sesión: en segundos si las hace desde la
plataforma); no se propagan los cambios de stop loss o take profit del gestor a posiciones ya copiadas; el resultado de una copia cerrada se actualiza con el registro
de operaciones del seguidor (hasta un minuto de retraso). Todo es solo demo.
"""
import math
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone

import configuracion
from herramientas import comisiones, gestor_autenticacion
from herramientas.backends import sesiones_capital
from herramientas.puente_mt5 import PROVEEDOR, cerrar_posicion, ejecutar_orden_mercado, obtener_info_cuenta, obtener_posiciones

_COPIAS = "copias"
_OPS = "copias_operaciones"
_OPERACIONES = "operaciones"
# Motor: nombre del hilo, evento para despertarlo y candado de arranque
_NOMBRE_HILO = "motor-copy-trading"
_DESPERTAR = threading.Event()
_CANDADO_MOTOR = threading.Lock()
_VERSION_TERMINOS = "1"


# TITULO ERROR COPIA

class ErrorCopia(Exception):
    """Se lanza cuando una acción de copia no se puede hacer (sin cuenta de inversor, importe bajo, estrategia no disponible, etc.). El mensaje es legible."""


# TITULO CLIENTE

def _cliente():
    """Cliente de Supabase, o `ErrorCopia` si no está configurado."""
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        raise ErrorCopia("El copy trading necesita la base de datos (Supabase), que no está configurada en este equipo.")
    return cliente


# TITULO AHORA

def _ahora() -> str:
    """Fecha y hora actual en UTC como texto ISO."""
    return datetime.now(timezone.utc).isoformat()


# TITULO A NUMERO

def _n(valor, defecto: float = 0.0) -> float:
    """Convierte a número (los numéricos de Supabase pueden llegar como texto); `defecto` si está vacío o es inválido."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


# TITULO DISPONIBLE

def disponible() -> bool:
    """True si el copy trading se puede usar en este equipo: hay Supabase y el modo multiusuario (cada seguidor opera en su propia cuenta)."""
    return gestor_autenticacion._supabase is not None and sesiones_capital.MULTIUSUARIO


# TITULO CUENTA DE INVERSOR

def cuenta_inversor(usuario_id) -> dict | None:
    """Fila de `cuentas_inversor` del usuario, o None si todavía no abrió su cuenta de inversor."""
    filas = _cliente().table("cuentas_inversor").select("*").eq("usuario_id", int(usuario_id)).limit(1).execute().data or []
    return filas[0] if filas else None


# TITULO ABRIR CUENTA DE INVERSOR

def abrir_cuenta_inversor(usuario_id, acepto: bool) -> dict:
    """Abre la cuenta de inversor del usuario (hay que aceptar los términos). Si ya la tenía, la devuelve. Lanza `ErrorCopia` si no aceptó."""
    existente = cuenta_inversor(usuario_id)
    if existente:
        return existente
    if not acepto:
        raise ErrorCopia("Para abrir una cuenta de inversor tienes que aceptar los términos y condiciones.")
    fila = {"usuario_id": int(usuario_id), "acepto_terminos_en": _ahora(), "version_terminos": _VERSION_TERMINOS, "estado": "activa"}
    _cliente().table("cuentas_inversor").insert(fila).execute()
    return fila


# TITULO ESCALAR VOLUMEN

def escalar_volumen(volumen_origen: float, base: float, copia: dict, minimo: float = 0.01, paso: float = 0.01, maximo: float | None = None) -> tuple:
    """Calcula el volumen (lotes) que le corresponde a la copia. Devuelve (volumen, motivo): volumen None y el motivo si no se puede copiar.

    `base` es el equity del gestor al abrir (solo se usa en el modo por importe). El resultado se redondea hacia abajo al `paso` y se limita a `maximo`."""
    if copia.get("modo") == "multiplicador":
        factor = _n(copia.get("multiplicador"))
    else:
        factor = _n(copia.get("importe")) / base if base > 0 else 0.0
    if factor <= 0:
        return None, "No se pudo calcular el tamaño (falta el equity del gestor)."
    bruto = volumen_origen * factor
    volumen = math.floor(bruto / paso + 1e-9) * paso
    if volumen < minimo - 1e-12:
        return None, f"El tamaño que te corresponde ({bruto:.4f} lotes) está bajo el mínimo del bróker ({minimo:g}); sube el importe o el multiplicador."
    if maximo is not None:
        volumen = min(volumen, maximo)
    return round(volumen, 6), ""


# TITULO REGLAS DE VOLUMEN

def _reglas_volumen(epic: str) -> tuple:
    """(mínimo, paso, máximo) de volumen en lotes del instrumento `epic` según el bróker; (0.01, 0.01, None) si no lo informa. Solo con Capital.com."""
    if PROVEEDOR != "capital":
        return 0.01, 0.01, None
    try:
        from herramientas.backends.capital_nucleo import factor_lote_epic, obtener_mercado
        reglas = (obtener_mercado(epic) or {}).get("dealingRules", {}) or {}
        factor = factor_lote_epic(epic) or 1.0
        minimo = _n((reglas.get("minDealSize") or {}).get("value"), 0.0) / factor
        paso = _n((reglas.get("minSizeIncrement") or {}).get("value"), 0.0) / factor
        maximo = _n((reglas.get("maxDealSize") or {}).get("value"), 0.0) / factor
        return (minimo or 0.01), (paso or minimo or 0.01), (maximo or None)
    except Exception:  # noqa: BLE001
        return 0.01, 0.01, None


# TITULO CREAR COPIA

def crear_copia(usuario_id, estrategia_id, modo: str, importe=None, multiplicador=None, copiar_abiertas: bool = False,
                take_profit_pct=None, stop_loss_pct=None, equity_cuenta: float | None = None, perfil_previo: dict | None = None) -> dict:
    """Crea la copia de una estrategia publicada para el usuario y devuelve su fila.

    Validaciones: tener cuenta de inversor, que la estrategia esté publicada y no sea propia, no copiarla ya, no superar las copias vigentes permitidas, un importe
    mínimo, un multiplicador válido y, si se indica `equity_cuenta` (equity de su cuenta demo), que el total asignado a todas sus copias no lo supere. El take profit y el
    stop loss (% del importe) exigen un importe. `perfil_previo` guarda el perfil de inversor anterior del seguidor, por si quiere restaurarlo al detener la copia. Lanza `ErrorCopia` si algo no se cumple."""
    cliente, cfg = _cliente(), configuracion.COPYTRADING
    if not cuenta_inversor(usuario_id):
        raise ErrorCopia("Primero abre tu cuenta de inversor.")
    estrategia = (cliente.table("estrategias").select("*").eq("id", int(estrategia_id)).eq("estado", "publicada").limit(1).execute().data or [None])[0]
    if not estrategia:
        raise ErrorCopia("Esa estrategia ya no está disponible para copiar.")
    if estrategia.get("cuenta_tipo", "demo") != "demo":
        raise ErrorCopia("Por ahora solo se pueden copiar estrategias de cuentas demo.")
    if int(estrategia["gestor_id"]) == int(usuario_id):
        raise ErrorCopia("No puedes copiar tu propia estrategia.")
    vigentes = cliente.table(_COPIAS).select("id,estrategia_id,importe").eq("inversor_id", int(usuario_id)).in_("estado", ["activa", "pausada"]).execute().data or []
    if any(int(c["estrategia_id"]) == int(estrategia_id) for c in vigentes):
        raise ErrorCopia("Ya estás copiando esta estrategia.")
    if len(vigentes) >= cfg["max_copias_por_inversor"]:
        raise ErrorCopia(f"Puedes tener hasta {cfg['max_copias_por_inversor']} copias a la vez. Detén una para crear otra.")
    if modo not in ("importe", "multiplicador"):
        raise ErrorCopia("El modo de asignación no es válido.")
    importe, multiplicador = (_n(importe) or None), (_n(multiplicador) or None)
    if modo == "importe":
        if not importe or importe < _n(estrategia["inversion_minima"]):
            raise ErrorCopia(f"El importe mínimo para copiar esta estrategia es ${_n(estrategia['inversion_minima']):,.0f}.")
    elif not multiplicador or multiplicador <= 0 or multiplicador > 100:
        raise ErrorCopia("El multiplicador debe estar entre 0 y 100.")
    if (take_profit_pct or stop_loss_pct) and not importe:
        raise ErrorCopia("El take profit y el stop loss de la copia se calculan sobre el importe invertido: indica un importe.")
    for etiqueta, valor in (("take profit", take_profit_pct), ("stop loss", stop_loss_pct)):
        if valor is not None and not 0 < _n(valor) <= (100 if etiqueta == "stop loss" else 10000):
            raise ErrorCopia(f"El {etiqueta} debe ser un porcentaje válido.")
    if equity_cuenta is not None and importe and sum(_n(c.get("importe")) for c in vigentes) + importe > equity_cuenta + 1e-9:
        raise ErrorCopia("Tu cuenta no tiene saldo suficiente para asignar ese importe junto con tus otras copias.")
    fila = {"inversor_id": int(usuario_id), "estrategia_id": int(estrategia_id), "modo": modo, "importe": importe, "multiplicador": multiplicador if modo == "multiplicador" else None,
            "copiar_abiertas": bool(copiar_abiertas), "take_profit_pct": _n(take_profit_pct) or None, "stop_loss_pct": _n(stop_loss_pct) or None, "estado": "activa", "perfil_previo": perfil_previo}
    try:
        creada = (cliente.table(_COPIAS).insert(fila).execute().data or [fila])[0]
    except Exception:  # noqa: BLE001
        raise ErrorCopia("No se pudo crear la copia. Inténtalo de nuevo.") from None
    despertar()
    return creada


# TITULO CAMBIAR ESTADO DE COPIA

def cambiar_estado_copia(usuario_id, copia_id, nuevo: str, cerrar_posiciones: bool = False) -> dict:
    """Pausa, reanuda o detiene una copia propia. Con `cerrar_posiciones` al detenerla el motor cierra también las posiciones abiertas de la copia."""
    cliente = _cliente()
    copia = (cliente.table(_COPIAS).select("*").eq("id", int(copia_id)).eq("inversor_id", int(usuario_id)).limit(1).execute().data or [None])[0]
    if not copia:
        raise ErrorCopia("No encontramos esa copia.")
    permitidas = {"activa": ("pausada", "cerrada"), "pausada": ("activa", "cerrada")}
    if nuevo not in permitidas.get(copia["estado"], ()):
        raise ErrorCopia(f"Una copia {copia['estado']} no puede pasar a {nuevo}.")
    if nuevo == "activa" and copia.get("motivo_cierre") == "comision_pendiente":
        estrategia = (cliente.table("estrategias").select("*").eq("id", copia["estrategia_id"]).limit(1).execute().data or [{}])[0]
        queda = comisiones.cobrar_pendientes(cliente, copia, estrategia)
        if queda > 0:
            raise ErrorCopia(f"Tienes ${queda:,.2f} de comisión pendiente. Recarga tu billetera virtual para reanudar la copia.")
        despertar()
        return copia
    cambios = {"estado": nuevo}
    if nuevo == "cerrada":
        cambios.update({"cerrada_en": _ahora(), "motivo_cierre": "usuario_cierra_posiciones" if cerrar_posiciones else "usuario"})
    cliente.table(_COPIAS).update(cambios).eq("id", copia["id"]).execute()
    despertar()
    return {**copia, **cambios}


# TITULO MIS COPIAS

def mis_copias(usuario_id) -> list:
    """Copias del usuario (las más nuevas primero), cada una con el `nombre` de la estrategia, el `gestor` (apodo), las `abiertas` (operaciones copiadas abiertas), las `cerradas`
    el `resultado` realizado (suma de las operaciones copiadas ya cerradas) y las comisiones `comision_pagada` y `comision_pendiente`."""
    cliente = _cliente()
    copias = cliente.table(_COPIAS).select("*").eq("inversor_id", int(usuario_id)).order("id", desc=True).execute().data or []
    if not copias:
        return []
    est = {e["id"]: e for e in cliente.table("estrategias").select("id,nombre,gestor_id,comision_pct").in_("id", list({c["estrategia_id"] for c in copias})).execute().data or []}
    apodos = {p["usuario_id"]: p.get("apodo") for p in cliente.table("perfiles_usuario").select("usuario_id,apodo").in_("usuario_id", list({e["gestor_id"] for e in est.values()})).execute().data or []}
    ops = cliente.table(_OPERACIONES).select("copia_id,estado,resultado").in_("copia_id", [c["id"] for c in copias]).execute().data or []
    coms = cliente.table("comisiones_rendimiento").select("copia_id,comision,movimiento_billetera_id").in_("copia_id", [c["id"] for c in copias]).execute().data or []
    salida = []
    for c in copias:
        propias = [o for o in ops if o["copia_id"] == c["id"]]
        e = est.get(c["estrategia_id"], {})
        salida.append({**c, "nombre": e.get("nombre", "Estrategia"), "comision_pct_estrategia": _n(e.get("comision_pct")), "gestor": apodos.get(e.get("gestor_id")) or "gestor", "abiertas": sum(1 for o in propias if o["estado"] == "abierta"),
                       "cerradas": sum(1 for o in propias if o["estado"] == "cerrada"), "resultado": round(sum(_n(o.get("resultado")) for o in propias if o["estado"] == "cerrada"), 2),
                       "comision_pagada": round(sum(_n(x["comision"]) for x in coms if x["copia_id"] == c["id"] and x.get("movimiento_billetera_id") is not None), 2),
                       "comision_pendiente": round(sum(_n(x["comision"]) for x in coms if x["copia_id"] == c["id"] and x.get("movimiento_billetera_id") is None), 2)})
    return salida


# TITULO OPERACIONES DE UNA COPIA

def operaciones_de_copia(usuario_id, copia_id, limite: int = 30) -> list:
    """Operaciones que se intentaron replicar en una copia propia, las más nuevas primero: [{"simbolo", "lado", "volumen_origen", "volumen_copia", "estado", "error", "fecha"}].

    Lanza `ErrorCopia` si la copia no es del usuario."""
    cliente = _cliente()
    if not (cliente.table(_COPIAS).select("id").eq("id", int(copia_id)).eq("inversor_id", int(usuario_id)).limit(1).execute().data or []):
        raise ErrorCopia("No encontramos esa copia.")
    filas = cliente.table(_OPS).select("*").eq("copia_id", int(copia_id)).order("id", desc=True).limit(limite).execute().data or []
    origen = {o["id"]: o for o in cliente.table(_OPERACIONES).select("id,simbolo,lado").in_("id", [f["operacion_origen_id"] for f in filas]).execute().data or []} if filas else {}
    return [{"simbolo": origen.get(f["operacion_origen_id"], {}).get("simbolo", ""), "lado": origen.get(f["operacion_origen_id"], {}).get("lado", ""),
             "volumen_origen": f.get("volumen_origen"), "volumen_copia": f.get("volumen_copia"), "estado": f.get("estado"), "error": f.get("error"),
             "fecha": f.get("creado_en")} for f in filas]


# TITULO EQUITY DEL GESTOR

def _equity_gestor(cliente, estrategia: dict, operacion: dict) -> float:
    """Equity del gestor al abrir la operación (el que se registró con ella) o, si falta, su última foto de equity; 0 si no hay ninguno."""
    base = _n(operacion.get("equity_apertura"))
    if base > 0:
        return base
    foto = (cliente.table("equity_historial").select("equity").eq("usuario_id", estrategia["gestor_id"]).eq("cuenta_tipo", estrategia.get("cuenta_tipo", "demo"))
            .order("id", desc=True).limit(1).execute().data or [{}])[0]
    return _n(foto.get("equity"))


# TITULO REGISTRAR OPERACION COPIADA

def _registrar_operacion_copiada(cliente, copia: dict, origen: dict, ticket: str, volumen: float, precio: float, equity: float | None) -> int | None:
    """Anota en `operaciones` la posición que se abrió para la copia (origen «copia») y devuelve su id. Si el registro de operaciones ya la había anotado como manual,
    la corrige. None si no se pudo anotar (la copia igual quedó abierta y se anotará como manual)."""
    fila = {"usuario_id": copia["inversor_id"], "cuenta_tipo": "demo", "id_broker": str(ticket), "simbolo": origen["simbolo"], "tipo_activo": origen.get("tipo_activo"),
            "lado": origen["lado"], "volumen": volumen, "precio_apertura": precio, "abierta_en": _ahora(), "stop_loss": origen.get("stop_loss"), "take_profit": origen.get("take_profit"),
            "equity_apertura": equity, "estado": "abierta", "origen": "copia", "copia_id": copia["id"], "operacion_origen_id": origen["id"]}
    try:
        return (cliente.table(_OPERACIONES).insert(fila).execute().data or [{}])[0].get("id")
    except Exception:  # noqa: BLE001 - el registro de operaciones se adelantó: se corrige su fila
        try:
            cliente.table(_OPERACIONES).update({"origen": "copia", "copia_id": copia["id"], "operacion_origen_id": origen["id"]}) \
                .eq("usuario_id", copia["inversor_id"]).eq("cuenta_tipo", "demo").eq("id_broker", str(ticket)).execute()
            return (cliente.table(_OPERACIONES).select("id").eq("usuario_id", copia["inversor_id"]).eq("cuenta_tipo", "demo").eq("id_broker", str(ticket)).limit(1).execute().data or [{}])[0].get("id")
        except Exception:  # noqa: BLE001
            return None


# TITULO ABRIR COPIAS

def _abrir_nuevas(cliente, copia: dict, estrategia: dict, equity_seguidor: float | None) -> int:
    """Replica en la cuenta del seguidor las operaciones abiertas del gestor que todavía no se copiaron. Devuelve cuántas abrió."""
    if copia["estado"] != "activa":
        return 0
    abiertas = cliente.table(_OPERACIONES).select("*").eq("usuario_id", estrategia["gestor_id"]).eq("cuenta_tipo", estrategia.get("cuenta_tipo", "demo")).eq("estado", "abierta").execute().data or []
    hechas = {o["operacion_origen_id"] for o in cliente.table(_OPS).select("operacion_origen_id").eq("copia_id", copia["id"]).execute().data or []}
    desde = str(copia.get("creada_en") or "")
    abiertas_ok = 0
    for o in sorted(abiertas, key=lambda x: str(x.get("abierta_en"))):
        if o["id"] in hechas or o.get("origen") == "copia":
            continue                                   # ya copiada, o es una copia de otra estrategia (no se encadenan)
        if not copia.get("copiar_abiertas") and str(o.get("abierta_en")) < desde:
            continue                                   # abierta antes de empezar a copiar
        fila = {"copia_id": copia["id"], "operacion_origen_id": o["id"], "volumen_origen": _n(o["volumen"]), "precio_origen": _n(o["precio_apertura"]), "estado": "pendiente"}
        try:
            cliente.table(_OPS).insert(fila).execute()           # se reclama antes de enviar la orden: si se interrumpe, no se repite
        except Exception:  # noqa: BLE001 - otro proceso la reclamó primero
            continue
        minimo, paso, maximo = _reglas_volumen(o["simbolo"])
        volumen, motivo = escalar_volumen(_n(o["volumen"]), _equity_gestor(cliente, estrategia, o), copia, minimo, paso, maximo)
        if volumen is None:
            cliente.table(_OPS).update({"estado": "fallida", "error": motivo, "actualizado_en": _ahora()}).eq("copia_id", copia["id"]).eq("operacion_origen_id", o["id"]).execute()
            continue
        resultado = ejecutar_orden_mercado(o["simbolo"], "BUY" if o["lado"] == "compra" else "SELL", volumen, _n(o.get("stop_loss")), _n(o.get("take_profit")))
        if "error" in resultado:
            cliente.table(_OPS).update({"estado": "fallida", "error": str(resultado["error"])[:300], "actualizado_en": _ahora()}).eq("copia_id", copia["id"]).eq("operacion_origen_id", o["id"]).execute()
            continue
        id_copia = _registrar_operacion_copiada(cliente, copia, o, resultado.get("order", ""), volumen, _n(resultado.get("price")), equity_seguidor)
        cliente.table(_OPS).update({"estado": "copiada", "volumen_copia": volumen, "precio_copia": _n(resultado.get("price")), "operacion_copia_id": id_copia,
                                    "actualizado_en": _ahora()}).eq("copia_id", copia["id"]).eq("operacion_origen_id", o["id"]).execute()
        try:
            from herramientas import registro_operaciones
            registro_operaciones.anotar_origen(resultado.get("order", ""), "copia")
        except Exception:  # noqa: BLE001
            pass
        abiertas_ok += 1
    return abiertas_ok


# TITULO CERRAR POSICION DE COPIA

def _cerrar_posicion_copia(cliente, copia: dict, fila_ops: dict, motivo_error: str = "") -> bool:
    """Cierra en el bróker la posición copiada de `fila_ops` (fila de copias_operaciones) y la marca cerrada. Devuelve True si se cerró (o ya no existía)."""
    ticket = None
    if fila_ops.get("operacion_copia_id"):
        r = (cliente.table(_OPERACIONES).select("id_broker").eq("id", fila_ops["operacion_copia_id"]).limit(1).execute().data or [None])[0]
        ticket = r["id_broker"] if r else None
    if not ticket:
        return False
    resultado = cerrar_posicion(ticket)
    if "error" in resultado and not any(t in str(resultado["error"]).lower() for t in ("404", "not found", "no existe", "error.not-found")):
        cliente.table(_OPS).update({"error": str(resultado["error"])[:300], "actualizado_en": _ahora()}).eq("id", fila_ops["id"]).execute()
        return False
    cliente.table(_OPS).update({"estado": "cerrada", "error": motivo_error or None, "actualizado_en": _ahora()}).eq("id", fila_ops["id"]).execute()
    if "error" not in resultado:
        # El resultado de la copia se anota al cerrar (no depende de que el seguidor tenga la plataforma abierta): la comisión se calcula con él.
        propia = (cliente.table(_OPERACIONES).select("precio_apertura").eq("id", fila_ops["operacion_copia_id"]).limit(1).execute().data or [{}])[0]
        cliente.table(_OPERACIONES).update({"estado": "cerrada", "precio_cierre": _n(resultado.get("level")) or _n(propia.get("precio_apertura")), "cerrada_en": _ahora(),
                                            "resultado": round(_n(resultado.get("profit")), 2), "actualizado_en": _ahora()}).eq("id", fila_ops["operacion_copia_id"]).execute()
    return True


# TITULO CERRAR LAS DEL GESTOR

def _cerrar_las_del_gestor(cliente, copia: dict) -> int:
    """Cierra en la cuenta del seguidor las posiciones copiadas cuya operación original ya cerró el gestor. Devuelve cuántas cerró."""
    copiadas = cliente.table(_OPS).select("*").eq("copia_id", copia["id"]).eq("estado", "copiada").execute().data or []
    if not copiadas:
        return 0
    origen = {o["id"]: o for o in cliente.table(_OPERACIONES).select("id,estado").in_("id", [c["operacion_origen_id"] for c in copiadas]).execute().data or []}
    return sum(1 for c in copiadas if origen.get(c["operacion_origen_id"], {}).get("estado") == "cerrada" and _cerrar_posicion_copia(cliente, copia, c))


# TITULO CERRAR TODAS DE LA COPIA

def _cerrar_todas(cliente, copia: dict) -> int:
    """Cierra todas las posiciones abiertas de la copia. Devuelve cuántas cerró."""
    copiadas = cliente.table(_OPS).select("*").eq("copia_id", copia["id"]).eq("estado", "copiada").execute().data or []
    return sum(1 for c in copiadas if _cerrar_posicion_copia(cliente, copia, c))


# TITULO PROTECCIONES

def _revisar_protecciones(cliente, copia: dict) -> str | None:
    """Revisa el take profit y el stop loss de la copia (% del importe). Si se alcanzó, cierra sus posiciones y la copia; devuelve "take_profit", "stop_loss" o None."""
    base = _n(copia.get("importe"))
    if base <= 0 or not (copia.get("take_profit_pct") or copia.get("stop_loss_pct")):
        return None
    ops = cliente.table(_OPERACIONES).select("id_broker,estado,resultado").eq("copia_id", copia["id"]).execute().data or []
    realizado = sum(_n(o.get("resultado")) for o in ops if o["estado"] == "cerrada")
    vivas = {str(p.get("ticket")): _n(p.get("profit")) for p in (obtener_posiciones() or [])}
    flotante = sum(vivas.get(str(o["id_broker"]), 0.0) for o in ops if o["estado"] == "abierta")
    pct = (realizado + flotante) / base * 100
    motivo = "take_profit" if copia.get("take_profit_pct") and pct >= _n(copia["take_profit_pct"]) else ("stop_loss" if copia.get("stop_loss_pct") and pct <= -_n(copia["stop_loss_pct"]) else None)
    if motivo:
        _cerrar_todas(cliente, copia)
        cliente.table(_COPIAS).update({"estado": "cerrada", "cerrada_en": _ahora(), "motivo_cierre": motivo}).eq("id", copia["id"]).execute()
    return motivo


# TITULO LIMPIAR PENDIENTES

def _limpiar_pendientes(cliente, copia: dict) -> None:
    """Marca como fallidas, sin reintentar, las operaciones que quedaron «pendientes» más de `pendiente_vence_s` segundos (una interrupción a mitad de la orden)."""
    limite = datetime.now(timezone.utc) - timedelta(seconds=configuracion.COPYTRADING["pendiente_vence_s"])
    for f in cliente.table(_OPS).select("id,actualizado_en,creado_en").eq("copia_id", copia["id"]).eq("estado", "pendiente").execute().data or []:
        try:
            hora = datetime.fromisoformat(str(f.get("actualizado_en") or f.get("creado_en")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if hora < limite:
            cliente.table(_OPS).update({"estado": "fallida", "error": "Interrumpida antes de confirmar la orden; no se reintenta para no duplicarla.", "actualizado_en": _ahora()}).eq("id", f["id"]).execute()


# TITULO PROCESAR COPIA

def procesar_copia(cliente, copia: dict, estrategia: dict) -> dict:
    """Una pasada sobre una copia, en la cuenta de su dueño (el llamador ya fijó la sesión): cierra lo que cerró el gestor, abre lo nuevo y revisa el take profit y el stop loss.

    Devuelve {"abiertas": n, "cerradas": n, "protegida": motivo o None, "comision": resultado de `comisiones.revisar`}. Una copia cerrada solo cierra sus posiciones si
    se pidió así; después liquida su comisión final."""
    resumen = {"abiertas": 0, "cerradas": 0, "protegida": None}
    if estrategia.get("cuenta_tipo", "demo") != "demo":
        return resumen               # nunca se replican operaciones de una cuenta real
    if copia["estado"] == "cerrada":
        if copia.get("motivo_cierre") == "usuario_cierra_posiciones":
            resumen["cerradas"] = _cerrar_todas(cliente, copia)
        resumen["comision"] = comisiones.revisar(cliente, copia, estrategia)
        return resumen
    _limpiar_pendientes(cliente, copia)
    resumen["cerradas"] = _cerrar_las_del_gestor(cliente, copia)
    info = obtener_info_cuenta() or {}
    resumen["abiertas"] = _abrir_nuevas(cliente, copia, estrategia, None if "error" in info else _n(info.get("equity")) or None)
    resumen["protegida"] = _revisar_protecciones(cliente, copia)
    resumen["comision"] = comisiones.revisar(cliente, copia, estrategia) if resumen["protegida"] is None else {}
    if resumen["protegida"] is not None:            # la copia acaba de cerrarse por su take profit o stop loss: pasa a la liquidación final en la próxima pasada
        copia["estado"] = "cerrada"
    return resumen


# TITULO PROCESAR TODAS

def procesar_todas() -> int:
    """Una pasada de todas las copias vigentes (y de las cerradas que pidieron cerrar sus posiciones). Cada copia se procesa en la cuenta demo de su dueño y un fallo en una
    no afecta a las demás. Devuelve cuántas procesó."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or not sesiones_capital.MULTIUSUARIO:
        return 0                     # sin modo multiusuario no hay cuenta propia de cada seguidor: copiar operaría siempre en la cuenta del .env
    copias = cliente.table(_COPIAS).select("*").in_("estado", ["activa", "pausada"]).execute().data or []
    cerradas = cliente.table(_COPIAS).select("*").eq("estado", "cerrada").execute().data or []
    con_pendiente = {f["copia_id"] for f in cliente.table("comisiones_rendimiento").select("copia_id,comision").is_("movimiento_billetera_id", "null").execute().data or [] if _n(f["comision"]) > 0}
    copias += [c for c in cerradas if not c.get("comision_final_en") or c["id"] in con_pendiente]     # las detenidas con liquidación o cobro por hacer
    procesadas = 0
    for copia in copias:
        try:
            estrategia = (cliente.table("estrategias").select("*").eq("id", copia["estrategia_id"]).limit(1).execute().data or [None])[0]
            if not estrategia:
                continue
            with sesiones_capital.con_clave((int(copia["inversor_id"]), True)):
                procesar_copia(cliente, copia, estrategia)
            procesadas += 1
        except Exception:  # noqa: BLE001 - se imprime y sigue con las demás copias
            traceback.print_exc()
    return procesadas


# TITULO DESPERTAR

def despertar() -> None:
    """Pide al motor una pasada inmediata (por ejemplo al crear una copia o cuando el registro anota operaciones nuevas)."""
    _DESPERTAR.set()


# TITULO BUCLE

def _bucle() -> None:
    """Bucle del hilo del motor: procesa las copias y espera `espera_motor_s` segundos o a que lo despierten; los errores se imprimen."""
    while True:
        try:
            procesar_todas()
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        _DESPERTAR.wait(configuracion.COPYTRADING["espera_motor_s"])
        _DESPERTAR.clear()
        time.sleep(0.2)


# TITULO INICIAR MOTOR

def iniciar_motor() -> bool:
    """Arranca el motor de copia si no está en marcha (idempotente, también si Streamlit recarga el módulo). Devuelve True si lo arrancó ahora."""
    if not sesiones_capital.MULTIUSUARIO:
        return False
    with _CANDADO_MOTOR:
        if any(t.name == _NOMBRE_HILO and t.is_alive() for t in threading.enumerate()):
            return False
        threading.Thread(target=_bucle, name=_NOMBRE_HILO, daemon=True).start()
        return True



# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara copiador .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
