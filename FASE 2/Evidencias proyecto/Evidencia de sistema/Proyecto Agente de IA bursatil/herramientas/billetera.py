# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara billetera .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Billetera virtual del usuario: saldo de prueba (sin valor monetario) y libro de movimientos.

Sirve para pagar planes dentro de la plataforma y deja armada la estructura para cuentas reales: cada movimiento tiene un tipo
(bono, recarga_virtual, compra_plan, ajuste, comision_pagada y comision_cobrada del copy trading y, para el futuro, deposito_real, retiro_real y resultado_operacion) y un monto con signo.

Dónde se guarda:
  - Modo multiusuario: en Supabase (tablas `billetera_cuentas` y `billetera_movimientos`, esquema en `herramientas/sql/billetera.sql`). Cada
    movimiento pasa por la función SQL `billetera_mover`, que bloquea la fila del usuario, impide saldos negativos y no repite un movimiento con la
    misma clave; así dos clics seguidos no cobran dos veces ni dejan el saldo mal.
  - Modo local (un solo usuario): en el archivo `billetera.json` de la carpeta del usuario, con escritura atómica y un candado en el proceso.
Los límites (bono inicial, recargas ofrecidas, tope mensual de recargas y saldo máximo) salen de `configuracion.BILLETERA`.
Todas las funciones públicas lanzan `ErrorBilletera` con un mensaje legible cuando algo no se puede hacer.
"""
import json
import os
import threading
from datetime import datetime, timezone

import configuracion
from herramientas import cuota_ia, gestor_autenticacion
from herramientas.backends import sesiones_capital
from herramientas.carpeta_usuario import carpeta_de

# Tablas y función de Supabase
_TABLA_MOVIMIENTOS = "billetera_movimientos"
_FUNCION_MOVER = "billetera_mover"
# Nombre del archivo del modo local
_ARCHIVO = "billetera.json"
# Candado de las escrituras locales dentro del proceso
_CANDADO = threading.Lock()
# Tipos de movimiento que entiende la billetera
TIPOS = ("bono", "recarga_virtual", "compra_plan", "ajuste", "deposito_real", "retiro_real", "resultado_operacion", "comision_pagada", "comision_cobrada")


# TITULO ERROR BILLETERA

class ErrorBilletera(Exception):
    """Se lanza cuando un movimiento no se puede hacer (saldo insuficiente, tope superado, plan no válido o sin conexión). El mensaje es legible."""


# TITULO AHORA

def _ahora() -> str:
    """Fecha y hora actual en UTC como texto ISO."""
    return datetime.now(timezone.utc).isoformat()


# TITULO DUEÑO

def _dueno():
    """Identifica al dueño de la billetera: ("supabase", id de usuario) en multiusuario o ("local", ruta del archivo) en modo local."""
    clave = sesiones_capital.clave_actual()
    if sesiones_capital.MULTIUSUARIO and len(clave) == 2:
        return "supabase", clave[0]
    carpeta = carpeta_de(clave)
    return "local", os.path.join(carpeta, _ARCHIVO)


# TITULO LEER LOCAL

def _leer_local(ruta: str) -> dict:
    """Contenido del archivo local ({"saldo": float, "movimientos": [...]}); uno vacío si no existe o está dañado."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, dict) and isinstance(datos.get("movimientos"), list):
            datos["saldo"] = round(float(datos.get("saldo", 0)), 2)
            return datos
    except (OSError, ValueError, TypeError):
        pass
    return {"saldo": 0.0, "movimientos": []}


# TITULO MOVER

def _mover(tipo: str, monto: float, concepto: str = "", referencia: str | None = None, clave_unica: str | None = None) -> float:
    """Registra un movimiento (monto con signo) y devuelve el saldo que queda. Lanza `ErrorBilletera` si dejaría el saldo negativo o no se pudo guardar."""
    if tipo not in TIPOS:
        raise ErrorBilletera("Tipo de movimiento no válido.")
    monto = round(float(monto), 2)
    if monto == 0:
        raise ErrorBilletera("El monto debe ser distinto de cero.")
    donde, ref = _dueno()
    if donde == "supabase":
        cliente = gestor_autenticacion._supabase
        if cliente is None:
            raise ErrorBilletera("La billetera no está disponible ahora (sin conexión con la base de datos).")
        try:
            filas = cliente.rpc(_FUNCION_MOVER, {"p_usuario": int(ref), "p_tipo": tipo, "p_monto": monto, "p_concepto": concepto,
                                                 "p_referencia": referencia, "p_clave": clave_unica}).execute().data or []
            return round(float(filas[0]["saldo_nuevo"]), 2)
        except Exception as e:  # noqa: BLE001
            if "saldo_insuficiente" in str(e):
                raise ErrorBilletera("Saldo insuficiente.") from None
            raise ErrorBilletera("No se pudo registrar el movimiento. Inténtalo de nuevo.") from None
    with _CANDADO:
        datos = _leer_local(ref)
        if clave_unica and any(m.get("clave_unica") == clave_unica for m in datos["movimientos"]):
            return datos["saldo"]
        nuevo = round(datos["saldo"] + monto, 2)
        if nuevo < 0:
            raise ErrorBilletera("Saldo insuficiente.")
        datos["saldo"] = nuevo
        datos["movimientos"].append({"tipo": tipo, "monto": monto, "saldo_despues": nuevo, "concepto": concepto, "referencia": referencia,
                                     "clave_unica": clave_unica, "creado_en": _ahora()})
        os.makedirs(os.path.dirname(ref) or ".", exist_ok=True)
        with open(ref + ".tmp", "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        os.replace(ref + ".tmp", ref)
        return nuevo


# TITULO ASEGURAR

def _asegurar() -> None:
    """Abre la billetera con el bono inicial la primera vez que se usa (el bono lleva una clave única: no se repite)."""
    bono = float(configuracion.BILLETERA.get("bono_inicial", 0))
    if bono <= 0:
        return
    donde, ref = _dueno()
    try:
        _mover("bono", bono, "Saldo inicial de prueba", clave_unica=f"bono-{ref}" if donde == "supabase" else "bono-inicial")
    except ErrorBilletera:
        pass


# TITULO SALDO

def saldo() -> float:
    """Saldo actual de la billetera del usuario (abre la billetera con el bono inicial si es la primera vez). 0 si no se pudo consultar."""
    _asegurar()
    donde, ref = _dueno()
    if donde == "local":
        return _leer_local(ref)["saldo"]
    cliente = gestor_autenticacion._supabase
    try:
        filas = cliente.table("billetera_cuentas").select("saldo").eq("usuario_id", int(ref)).limit(1).execute().data or []
        return round(float(filas[0]["saldo"]), 2) if filas else 0.0
    except Exception:  # noqa: BLE001
        return 0.0


# TITULO MOVIMIENTOS

def movimientos(limite: int = 50) -> list:
    """Últimos `limite` movimientos, del más reciente al más antiguo: lista de {"creado_en", "tipo", "monto", "saldo_despues", "concepto"}. Vacía si no hay o no se pudo consultar."""
    donde, ref = _dueno()
    if donde == "local":
        return list(reversed(_leer_local(ref)["movimientos"]))[:limite]
    cliente = gestor_autenticacion._supabase
    try:
        return cliente.table(_TABLA_MOVIMIENTOS).select("creado_en,tipo,monto,saldo_despues,concepto").eq("usuario_id", int(ref)) \
            .order("creado_en", desc=True).order("id", desc=True).limit(limite).execute().data or []
    except Exception:  # noqa: BLE001
        return []


# TITULO RECARGADO EN EL MES

def recargado_en_el_mes() -> float:
    """Total recargado (recargas virtuales) en el mes en curso, en la moneda de la billetera."""
    mes = datetime.now(timezone.utc).strftime("%Y-%m")
    return round(sum(float(m.get("monto", 0)) for m in movimientos(1000)
                     if m.get("tipo") == "recarga_virtual" and str(m.get("creado_en", ""))[:7] == mes), 2)


# TITULO RECARGAR VIRTUAL

def recargar_virtual(monto: float) -> float:
    """Suma `monto` de saldo de prueba y devuelve el saldo nuevo. Respeta el tope mensual de recargas y el saldo máximo de `configuracion.BILLETERA`."""
    monto = round(float(monto), 2)
    if monto <= 0:
        raise ErrorBilletera("El monto debe ser mayor que cero.")
    cfg = configuracion.BILLETERA
    actual = saldo()
    if actual + monto > float(cfg["saldo_maximo"]):
        raise ErrorBilletera(f"El saldo no puede superar {cfg['saldo_maximo']:,.0f} {cfg['moneda']} en la billetera de prueba.".replace(",", "."))
    if recargado_en_el_mes() + monto > float(cfg["recarga_mensual_max"]):
        raise ErrorBilletera(f"Superas el tope de recargas de este mes ({cfg['recarga_mensual_max']:,.0f} {cfg['moneda']}).".replace(",", "."))
    return _mover("recarga_virtual", monto, "Recarga de saldo de prueba")


# TITULO COMPRAR PLAN

def comprar_plan(plan: str, precio: float) -> float:
    """Cobra `precio` de la billetera y activa el plan `plan` (origen «pago»). Devuelve el saldo que queda.

    Si el plan no se pudo activar después de cobrar, devuelve el dinero con un ajuste y lanza `ErrorBilletera`. Hoy es una compra de demostración
    de un mes: todavía no hay renovación ni vencimiento automáticos."""
    if plan not in configuracion.PLANES_IA or plan == "gratis":
        raise ErrorBilletera("Ese plan no se puede comprar.")
    precio = round(float(precio), 2)
    if precio <= 0:
        raise ErrorBilletera("El precio del plan no es válido.")
    nombre = configuracion.PLANES_IA[plan].get("nombre", plan)
    _asegurar()
    nuevo = _mover("compra_plan", -precio, f"Plan {nombre} · 1 mes (demostración)", referencia=plan)
    if not cuota_ia.fijar_plan(plan, "pago"):
        _mover("ajuste", precio, f"Reembolso: no se pudo activar el plan {nombre}", referencia=plan)
        raise ErrorBilletera("No se pudo activar el plan; te devolvimos el saldo.")
    return nuevo


# TITULO SALDO DE UN USUARIO

def saldo_usuario(usuario_id) -> float:
    """Saldo de la billetera del usuario `usuario_id` (cualquiera, no solo el actual); 0 si no tiene billetera o no se pudo consultar. Solo con Supabase."""
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        return 0.0
    try:
        filas = cliente.table("billetera_cuentas").select("saldo").eq("usuario_id", int(usuario_id)).limit(1).execute().data or []
        return round(float(filas[0]["saldo"]), 2) if filas else 0.0
    except Exception:  # noqa: BLE001
        return 0.0


# TITULO TRANSFERIR

def transferir(origen_id, destino_id, monto: float, concepto_origen: str, concepto_destino: str, referencia: str | None = None, clave_unica: str | None = None) -> int:
    """Pasa `monto` de la billetera de `origen_id` a la de `destino_id` en una sola operación y devuelve el id del movimiento del origen.

    Se usa para pagar comisiones del copy trading (el origen registra `comision_pagada` y el destino `comision_cobrada`). Con `clave_unica` repetir la llamada no vuelve
    a mover dinero. Solo funciona con Supabase (la función SQL `billetera_transferir`). Lanza `ErrorBilletera` si no hay saldo suficiente o no se pudo registrar."""
    monto = round(float(monto), 2)
    if monto <= 0:
        raise ErrorBilletera("El monto debe ser mayor que cero.")
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        raise ErrorBilletera("Las transferencias necesitan la base de datos (Supabase).")
    try:
        filas = cliente.rpc("billetera_transferir", {"p_origen": int(origen_id), "p_destino": int(destino_id), "p_monto": monto, "p_concepto_origen": concepto_origen,
                                                     "p_concepto_destino": concepto_destino, "p_referencia": referencia, "p_clave": clave_unica}).execute().data or []
        return int(filas[0]["movimiento_origen_id"])
    except Exception as e:  # noqa: BLE001
        if "saldo_insuficiente" in str(e):
            raise ErrorBilletera("Saldo insuficiente.") from None
        raise ErrorBilletera("No se pudo registrar la transferencia. Inténtalo de nuevo.") from None


# TITULO RESUMEN

def resumen() -> dict:
    """Totales del libro de movimientos: {"saldo", "recargado", "gastado_planes", "movimientos"} (cantidad de movimientos)."""
    movs = movimientos(1000)
    return {"saldo": saldo(), "recargado": round(sum(float(m["monto"]) for m in movs if m.get("tipo") == "recarga_virtual"), 2),
            "gastado_planes": round(-sum(float(m["monto"]) for m in movs if m.get("tipo") == "compra_plan"), 2), "movimientos": len(movs)}



# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara billetera .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
